# 概念

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

Pod 是什么？（最小运行单位）

Pod = Kubernetes 运行你的容器的最小单位。

每个 Pod：有自己的 IP,自己的网络环境,自己的文件系统

可以包含 1~多个 container（通常 1 个）

- Pod = mini 虚拟机环境
- Container = 在里面跑的进程

你实际运行的是容器，但你管理的是 Pod。

### Container

Container = 你的应用实际运行的地方（隔离进程）。

是由镜像启动的, 在 Pod 内运行. 内部 rootfs 独立,使用宿主机 kernel, 网络由 Pod 提供

一般一个 Pod 就一个 container（最佳实践）。有时会多个（sidecar、日志代理等）。

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

