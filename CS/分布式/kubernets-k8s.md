# k8s 历史

乃 Google 的 Borg 系统的开源版本

- 2000 — 2013：Kubernetes 的前身在 Google 内部诞生。Borg（2003~），Omega（2013）。
- 2014：Docker 火了，Kubernetes 应运而生
- 2015 — 2017：Kubernetes 超越所有竞争对手
- 2018 — 2020：进入云原生时代，大量项目围绕 Kubernetes 发展
- 2020 — 现在：Docker 被移除，containerd 成主流

# 基本概念

### Cluster

Kubernetes Cluster = 多台机器 组成一个集群。

这些机器包含：1 台或多台 Master / Control Plane 节点；多台 Worker Node（工作节点）

一套 K8s 集群里可以放很多项目

### node

Node = 一台机器（物理机或虚拟机）。

你可以理解成：一台云服务器；一台 VM；或一台实体 Linux 主机

每个 Node 上都能运行 Pods（容器）。

### Deployment

Deployment 不是“由很多 Node 组成”。而是一种 Kubernetes 对应用的管理方式，用来告诉 Kubernetes：
```
我要运行这个容器（镜像），
我要运行多少份，
要求一直保持运行，
更新版本要滚动更新。
```

它会创建 Pod，然后由 Kubernetes 决定把这些 Pod 分配到哪些 Node 上。

```
Kubernetes Cluster (由多台 Node 组成)
│
├── Node A
│     └── Pod 1  ← Deployment 创建
│
├── Node B
│     ├── Pod 2  ← Deployment 创建
│     └── Pod 3  ← Deployment 创建
│
└── Node C
      └── Pod 4  ← Deployment 创建
```
你会发现：

- Cluster = 多台机器
- Node = 单台机器
- Deployment = 创建和管理 Pod
- Pod 会被调度到 不同 Node 上运行

一个 Deployment 用来定义需要运行多少个 Pod 的！
Deployment 的职责很明确：
- 确保 Pod 数量。比如 replicas=5，就保证永远有 5 个 Pod 在跑。
- 自动修复。Pod 挂了 → 自动拉起新的。
- 自动滚动更新。升级镜像时，一个一个替换，不中断服务。

总结：

Deployment = 负责保证特定数量的 Pod 一直健康运行。
Deployment = 一份应用的运行配置（定义应用应该怎样运行、运行多少份、如何更新）。不直接指定运行的硬件（Cluster / Node 真正提供 CPU、内存、硬件的机器）

### Namespace

Namespace = K8s 集群里的“虚拟隔离空间（文件夹）”。

它用于把你的资源隔离开：
- 不同团队用不同 namespace
- 资源命名互不冲突
- 权限可以单独控制
- 一套 K8s 集群里可以放很多项目

可以类比：云里的不同环境：dev / test / prod

K8s 默认有这些 namespace：

default

kube-system

kube-public

你创建 Pod、Deployment 时都属于某个 namespace。

### pod

Pod 是什么？（最小运行单位）Pod 小得多、轻得多，它不是一台机器，也不是虚拟机，≠ 机器 instance。一个 node 可以运行多个 pod。可以把它看作运行你的应用的一次“实例”。对 Pod 内的进程来说，它“感觉”自己在一台独立的机器里。一个 Pod 可以跑多个容器；一个容器也可以跑多个进程。

Pod = Kubernetes 运行你的容器的最小单位。

每个 Pod：有自己的 IP,自己的网络环境。

可以包含 1~多个 container（通常 1 个）

- Pod = mini 虚拟机环境
- Container = 在里面跑的进程

你实际运行的是容器，但你管理的是 Pod。pod 本义是豆荚，那么 container 就是豆子。

### Container

Container = 你的应用实际运行的地方（隔离进程）。

是由镜像启动的, 在 Pod 内运行. 内部 rootfs 独立,使用宿主机 kernel, 网络由 Pod 提供。在 k8s 中，文件系统（rootfs）属于 container，不属于 pod。pod内多个容器可以共享 volume，但根文件系统不共享。shell 登录进去的是container 的 shell。

一般一个 Pod 就一个 container（最佳实践）。有时会多个（sidecar、日志代理等）。

pod 于 container 关系：
```
Pod
 ├─ Container A
 │    ├─ process A1 (PID 1)
 │    ├─ process A2 (fork)
 │    └─ process A3 (fork)
 └─ Container B
      ├─ process B1 (PID 1)
      └─ process B2 (fork)
```

namespace, deployment, replicaset, pod, container 关系：
```
Namespace
└── Deployment
      └── ReplicaSet
            └── Pod
                 └── Container
Node（实际机器）
└── 运行 Pod

Service
└── 为一组 Pod 提供一个统一入口
```

#### 问题：Kubernetes 本质是“容器编排系统”，管理的是 container，为什么要引入 pod？

但是容器本身 没有：
- IP（容器只有临时网络）
- 生命周期管理（容器挂了没法自动重启）
- 健康检查机制
- Sidecar 功能
- 共享 volumes、共享网络的能力

于是 Kubernetes 增加了一个概念： Pod = Kubernetes 管理容器的基本单元，是容器的“包装盒”。

【历史上看：Google 在 Borg 内部发现：每个应用如果直接管理容器，会非常混乱，应用通常需要多个容器协作：日志收集，代理，sidecar，init 程序，调试工具等，这些容器 必须共享网络（localhost）和部分存储，行为像一个整体。但容器本身做不到多容器共享网络】

#### docker 和 container 啥关系？

container 完全不需要是 Docker。k8s 容器运行时 (Container Runtime) 必须符合 CRI（Container Runtime Interface）规范。只要符合 CRI，K8s 就能运行它，不管是不是 Docker。k8s 现在反而现在不直接支持 docker，早就不直接支持 Docker Runtime 了。

containerd 才是 Docker 内部真正用来运行容器的底层部分。

----

# 所跑的任务

<img width="557" height="145" alt="image" src="https://github.com/user-attachments/assets/2dabbeac-2b69-455d-bf07-fdd836f08736" />

### Cron Job（Cron作业）

只在定时触发时创建 Pod；任务结束后 Pod 退出并清理，其余时间不占资源。

### Job（作业）

一次性的。Job 是一次性任务控制器，负责创建 Pod → 等 Pod 完成 →（可选）清理 Pod。

### 守护程序集（DaemonSet）

常驻、不退出，持续干活的后台服务。

常用于：
- 节点监控（如 Prometheus Node Exporter）
- 日志采集（如 Fluentd / Logstash）
- kube-proxy / CNI 组件

note：
- 业务 Server 模块（提供 API 服务、处理请求、完成任务的长期运行服务）应该使用： **Deployment**，这是 Kubernetes 中 最标准、最推荐 用来部署业务服务的控制器。
- DaemonSet，是每个node（机器）都要部署一个。会作为一个 pod 形式，在 node 上存在。

### StatefulSet

用来跑 “有状态” 的长期服务（比如 MongoDB），每个 Pod 都有固定名字 + 固定存储 + 固定顺序。

那 Deployment 为什么不能跑数据库？因为 Deployment 的 Pod：是匿名的，名字随机，重启可能会换名字；存储卷不是固定绑定的，这对数据库是灾难（会丢数据/乱序/集群混乱）。

note：

Azure 上购买的 Cosmos DB 不是以 StatefulSet 启动的。StatefulSet 是 Kubernetes 的一种控制器，用来管理你自己在 K8s 集群内部运行的数据库：例如：你自己部署 MySQL/redis/ES/kafka → 用 StatefulSet。这些都属于自建服务。

----

# 关于 k8s 的 client

### k9s

它是一个在终端里管理 Kubernetes 集群的可视化工具，比 kubectl 更高效、更好用。它让 Kubernetes 使用体验更像一个仪表盘。

`kubectl config use-context $content_name` 的执行局结果（不做修改），会影响 `k9s` 的查看吗?

会影响。因为 k9s 本质上是基于 kubectl 的 ~/.kube/config 文件运行的。kubectl 指向哪个集群，k9s 默认也会指向哪个集群

----

# k8s 的一些原理

### 最终一致

Kubernetes 是一个“最终一致性系统”，而不是按步执行命令的系统。

Kubernetes 不执行命令，它只不断比较：“期望状态（你写在 YAML 里的）” 和 “当前实际状态”，然后让系统自动把实际状态调和到期望状态。【你告诉它：`我要 5 个副本（replicas = 5）`,它会不断检查集群实际状态：`当前 3 个？那就再调度 2 个;如果死掉 1 个？它再补 1 个`。它永远尝试让实际状态逼近目标状态】这是 Google 在 Borg 时代学到的：分布式系统不能依赖即时命令（imperative），必须基于最终一致性。

Kubernetes 永远不执行一次性命令，只管理状态。

### master

```
             Control Plane（分布式，可多副本）
   ┌──────────────┬───────────────┬───────────────┐
   │  API Server  │   Controller  │   Scheduler   │
   └──────────────┴───────────────┴───────────────┘
                       │
                    etcd（强一致）
                       │
             Worker Nodes（Kubelet + KubeProxy）

```

Kubernetes 的 master 组件中：
- API Server 多个 master 同时发挥作用（全部 active）
- Scheduler / Controller Manager 是单 leader 工作；
- etcd 是多节点协作，但只有 1 个 leader 负责写入。

Master（控制平面）和 Worker（节点）不是两套完全独立的代码，而是“同一套 Kubernetes 项目里的不同组件”，分别运行在不同节点上。
