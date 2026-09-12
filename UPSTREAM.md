# Upstream

- Repository: `https://github.com/Dagherbou/OptiScaler_DLSSNR`
- Development branch: `dlss-neural-rendering`
- Stable channel: latest non-draft, non-prerelease GitHub Release

本仓库只维护本地化层、扫描/构建/发布工具和语言资源。CI 在干净环境拉取指定上游 ref。

DLSSNR Fork 的正式打包使用其自带 `package_release.ps1`，以保留 forwarder、文档及上游的安全检查；`nvngx_dlssnr.dll` 不会被打包。
