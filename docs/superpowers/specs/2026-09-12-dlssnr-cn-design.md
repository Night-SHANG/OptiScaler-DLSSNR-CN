# OptiScaler DLSSNR CN Design

目标：复用 OptiScaler-CN 的低侵入本地化框架维护 `Dagherbou/OptiScaler_DLSSNR`。

架构：仓库不复制上游源码；master/stable 各保存 UI catalog，共用 zh-CN；CI 拉取精确 ref，扫描、注入、编译 forwarder + solution，再调用上游 package_release.ps1 打包。

失败策略：关键源码锚点、扫描校验、forwarder/solution 编译或上游打包失败时停止 Release。专有 `nvngx_dlssnr.dll` 永不进入发布包。
