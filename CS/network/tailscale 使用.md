tailscale 可用于隧穿内网(穿越 NAT). 

### 它的好处

用使用侧, 在于构建了一个 100.x.x.x 的虚拟局域网(VPN), 给每个机器一个固定100ip, 以及一个容易记住的 magicDNS 域名. 被它管理的机器, 无论多远, 都可以直接访问, 仿佛是同一个物理内网一样. 

它是基于端到端加密的, 所以安全有保障, 不怕数据泄漏.

### 关于隧穿

不考虑隧穿, 他就是个 VPN. 它的牛逼在于令两个节点的访问成本最小化: 如果能 NAT 穿越, 则直连; 否则自动降级成 DERP 中转模式, 且中转模式下, 仍然会自动选用通信成本最小的derp 节点. 这样同一个内网之间的机器上, 用它自动就是本地互联. 

### 网络协议

tailscale 拼命想打洞成功走 p2p. 
- 打洞成功就会走 UDP.
- 如果失败走 DERP: 则是用 client 用 TCP 和 DERP server 交互, tcp 包里却是 udp, 以方便 WireGuard 层; 在更高层, 再次组合成 TCP(这就是著名的 "TCP-over-UDP-over-TCP" 三明治). 

也就是说, Tailscale 的内部抽象是 "一根能传输 UDP datagram 的管子"。WireGuard 协议在这根管子上跑。这根管子优先用真 UDP（直连）；做不到就用 TCP/TLS 伪装出一根虚拟的 UDP 管子（DERP）。

### 验证通了

- 看是否通: 两种方式 (1). `ping 100.x.x.x` (2). `tailscale ping 100.x.x.x`
- 看所用的 derp: 用 `taiscale netcheck`; 会用 latency 最小的那个

### 使用

设备上安装 tailscale client, 并登陆自己账号; 则自己账号下的所有设备自动在一个 VPN 局域网内了. 

----

###  自建 Tailscale 私有 DERP 中转节点 — Aliyun 实战版

## 现状速览（参考样本）

- 主机：Aliyun ECS（Ubuntu 22.04），公网 IP **x.x.x.x**
- DERP 进程：`/root/go/bin/derper` by systemd
- 证书：**自签名 10 年证书**（CN=IP，SAN=IP:x.x.x.x），不依赖域名/Let's Encrypt
- 监听端口：`443/tcp`（DERP over HTTPS）、`80/tcp`、`3478/udp`（STUN）
- netcheck 显示：`ali-cn: 500µs (Alibaba China)` — 已是 tailnet 内的"最近 DERP"

## 部署步骤

### 0. 前置准备
- 一台有公网 IP 的 VPS（推荐阿里云/腾讯云）
- 安全组放行：**TCP 80、TCP 443、UDP 3478**
- 系统：Ubuntu 22.04 / Debian 12 即可

### 1. 装 Go 并编译 derper
```bash
apt update && apt install -y wget tar
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
go install tailscale.com/cmd/derper@latest
# 产物：/root/go/bin/derper
```

### 2. 装 Tailscale 守护进程（必需）
`-verify-clients` 模式下，derper 通过本机 `tailscaled` 校验访问者是否在你的 tailnet：
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up   # 用你的 Tailscale 账号登录
```

### 3. 生成自签证书（用公网 IP 当 hostname）
```bash
PUBIP=x.x.x.x    # 改成你自己的公网 IP
mkdir -p /etc/derper/certs
openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
  -keyout /etc/derper/certs/${PUBIP}.key \
  -out    /etc/derper/certs/${PUBIP}.crt \
  -subj   "/CN=${PUBIP}" \
  -addext "subjectAltName=IP:${PUBIP}"
chmod 600 /etc/derper/certs/${PUBIP}.key
```
**关键点**：文件名必须是 `<hostname>.crt` / `<hostname>.key`，derper 会按 `-hostname` 参数到 `-certdir` 找同名文件。

### 4. systemd 单元

`/etc/systemd/system/derper.service`：
```ini
[Unit]
Description=Tailscale DERP Server
After=network.target

[Service]
ExecStart=/root/go/bin/derper -a :443 -http-port 80 -certmode manual \
  -certdir /etc/derper/certs -hostname x.x.x.x \
  -stun -stun-port 3478 -verify-clients
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：
```bash
systemctl daemon-reload
systemctl enable --now derper
systemctl status derper
```

各参数：
- `-a :443` — DERP 主流量入口（HTTPS）
- `-http-port 80` — 健康检查/引导用
- `-certmode manual` — 用自己的证书（不走 Let's Encrypt）
- `-stun -stun-port 3478` — 同时跑 STUN，加速直连
- `-verify-clients` — 只允许 **本 tailnet 的成员**使用，防止被白嫖

### 5. 在 Tailscale 控制台配置 Custom DERP

去 https://login.tailscale.com/admin/acls ，在 ACL 里加入：

```jsonc
{
  "derpMap": {
    "OmitDefaultRegions": false,   // 想完全独占就设 true
    "Regions": {
      "900": {
        "RegionID":   900,
        "RegionCode": "ali-cn",
        "RegionName": "Alibaba China",
        "Nodes": [{
          "Name":             "ali-cn-1",
          "RegionID":         900,
          "HostName":         "x.x.x.x",
          "IPv4":             "x.x.x.x",
          "InsecureForTests": true,    // 因为是自签证书
          "STUNPort":         3478,
          "DERPPort":         443
        }]
      }
    }
  }
}
```

> `RegionID` 自定义节点必须 ≥ 900；官方区是 1–899。
>
> `InsecureForTests: true` 是用自签证书时必加，否则客户端拒绝连接。
>
> 更正式的做法是把证书的 SHA256 指纹放进 `CertName`/`CertSHA256`，但 `InsecureForTests` 简单可用。

### 6. 验证

任一 tailnet 设备上跑：
```bash
tailscale netcheck
```

看到自定义 region（例：`ali-cn`）出现在列表里，且延迟最低，就成了。

## 维护清单

| 事项 | 命令/位置 |
|---|---|
| 日志 | `journalctl -u derper -f` |
| 重启 | `systemctl restart derper` |
| 升级 derper | `go install tailscale.com/cmd/derper@latest && systemctl restart derper` |
| 证书续期 | 10 年有效，到期前重新跑 step 3 的 openssl 即可 |
| 持久化 derper key | 自动存在 `/var/lib/derper/derper.key`（首次启动生成，不要删） |

## 几个容易踩的坑

1. **`-hostname` 必须和证书 CN/SAN 一致**，且当 hostname 是 IP 时，SAN 要写 `IP:x.x.x.x` 而不是 `DNS:x.x.x.x`。
2. **必须装 tailscaled 并登录**，否则 `-verify-clients` 启动失败。
3. **阿里云安全组**别忘了开 UDP/3478，否则 STUN 不通，直连成功率下降。
4. **国内云的 80/443 备案问题**：DERP 不走 HTTP 网页服务、不返回 HTML，理论上不触发备案校验，但谨慎起见可换非标准端口（如 `-a :8443`，记得 derpMap 里同步改 `DERPPort`）。
5. 如果只想自己的 tailnet 走自建 DERP，可在 ACL 把 `OmitDefaultRegions` 设为 `true`，但建议保留官方 DERP 作为 fallback。
