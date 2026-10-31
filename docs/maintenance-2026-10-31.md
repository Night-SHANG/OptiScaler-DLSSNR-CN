# DLSSNR 汉化覆盖审计（2026-10-31）

## 上游证据与边界

- 本仓基线：`a525c3071bb31d8955a6e1014562278df6baac3b`。
- 官方跟踪仓仍为 `Dagherbou/OptiScaler_DLSSNR`，分支仍为 `dlss-neural-rendering`。
- 本轮核验分支 SHA：`973761621353b99bee3dc7d4bb27b117fef2644f`，与本仓扫描记录一致。
- GitHub Release API 选中的最新正式版仍为 `v0.2.0-dlssnr`，指向同一 SHA。
  `v0.2.0-patch1` 同样指向此 SHA，但不能仅凭 tag 名称将其当成新的正式 Release。
- 此仓为本地化 overlay，不复制整个上游，也不从 PreSR/F5 fork 混入功能。
- 本轮没有推送、触发远程构建或发布；不分发 NVIDIA 专有 `nvngx_dlssnr.dll`。

## 为什么原先“词库 100%”仍有漏译

独立清点源码里的 UI 调用、数组、变量、帮助函数，再与扫描结果比较，发现：

1. `DlssNr_Menu.cpp` 自定义 `HelpMarker` / `DeferredSlider` 不在旧调用规则中；
   29 段详细帮助和延迟滑块标签没有进入清单。
2. `fnmatch` 的 `dlssnr/**/*.cpp` 不匹配直接位于 `dlssnr/` 的菜单文件。
   补显式 `dlssnr/*.cpp`，覆盖模型风格、缩放、对比等选项数组。
3. `snprintf` 生成的纸白校准标签、锚点行、编辑提示，和变量保存的重置按钮、
   模型隐藏状态、屏幕左右对比标签，均需额外覆盖。
4. 核心失败原因和曝光扫描状态不是直接 UI 字面量。
   仅将明确来源纳入词库，保留核心代码/日志英文；在菜单显示边界作翻译，
   持有 `std::string` 后再取 `c_str()`，避免临时对象悬空。
5. `ImGuiToast` / `InsertNotification` 构造式内容没有被 `.setContent` 规则覆盖。
   新扫描器只读取第三个内容字段；嵌套 `std::format` 整体改为运行时 `Loc::F`，
   不能只将 format 字面量改为 `Loc::T`。
6. 相邻 C++ 字面量应当作为一个表达式重写；分别改成两个 `T(...)` 会破坏编译。
   空白/注释分隔的相邻字面量已合并，并有回归。
7. 方法式条件参数 `toast.setContent(cond ? "On" : "Off")` 需要特殊匹配点号前缀；
   通用名称的负向边界不能直接套在方法名上。
8. 通用菜单内先声明再赋值的 FG 选项容器、预设/时序 helper、Keybind、
   状态文本拼接和文字测量亦补入审计范围。

## 保持不变的契约

- 原有 `zh-CN` 条目逐项比较，不改动旧译文。
- 缺译/源哈希过期时继续英文回退；字体选择和缺中文字体回退逻辑未改。
- 参数类型、DLL/API 名、内部枚举、配置字段、隐藏 `##` 后缀不翻译。
- Keybind 构造时保留原名称，显示时翻译并使用 `###原名称` 保持 widget ID。
- 新增诊断文字仅在 UI 边界翻译，不修改失败原因的核心存储/日志。
- 新规则限定到经过审查的文件、变量、函数；不全局重写任意字符串赋值。

## 验证方法

- `python -m compileall -q tools tests`
- `python -m unittest discover -s tests -q`
- 对同一已核 SHA 分别扫描 master/stable；检查 pending、哈希、printf/std::format 占位符及隐藏 ID。
- `python tools/check_localization.py --channel all --strict`
- `python tools/update_translation_memory.py --check`
- 对干净上游 git worktree 执行实际 `localize_source.py`，检查注入锚点、格式表达式和核心诊断文件未修改。
- 全量扫描清单覆盖率只表示“已识别字符串”覆盖，不等同于游戏内所有动态 UI 已实测。

## 尚需外部验收

本云环境不能替代 Windows/MSBuild Release 构建、实际 GPU/DLL 运行、
游戏内字体和窗口布局检查。尤其新增的长帮助文本及不同 DPI 下的显示，
必须在 Windows 构建和游戏内人工验证后才能称为最终发布验收完成。

## 本轮最终本地结果与残余边界

- master/stable 均为 1036 个 active 源条目，missing=0、stale=0；
  其中 373 reviewed、663 为既有 machine_translated 状态。
- 新增 137 条译文；逐项比较原有条目，修改数为 0。
- 81 个 unittest、compileall、严格占位符/隐藏 ID 校验、翻译记忆一致性、
  两通道 C++ 字典生成均通过。
- 对两个独立干净 worktree 实际注入；最终稳定通道注入 994 处字面量成功。
  29 个 NR HelpMarker、4 个 DeferredSlider 的包装有显式断言；
  所有注入 cpp 未发现 std::format(Loc::T(...))；
  核心 Dx12 失败原因文件和曝光扫描生产者文件字节未改。
- 额外修复了“先包装 %s，再精确匹配原始 tooltip 调用”导致动态帮助未翻译的顺序问题。
- 不把此结果称为游戏内汉化全部完成。独立审计仍记录小范围残余：
  通用菜单 join_with 的英文连接词 ` or `，放大镜滑块格式中的
  `of screen`，目前不在扫描清单内；技术缩写、API枚举、纯数值格式和日志有意保持原样。
  这两种混合/组合显示需后续窄范围扩展，并重新执行双通道扫描和注入。
- Windows 编译、游戏内功能/布局验收未执行；已有 machine_translated 条目不代表本轮逐条人工重审。

## 远端触发风险

- 向非 main/master 的维护分支 push 本身不匹配 build/upstream-sync 的 push 分支条件。
- 创建 PR（包括 draft）会匹配 build.yml 的 pull_request 和 localization-check.yml；
  是否构建依赖 GitHub 的事件/权限环境，需先获得授权。
- main/master 上的 Localization/overlay/tools/workflow/upstream.json 变化会触发 build；
  stable目录变化还会触发 upstream-sync，它拥有写权限，并可能继续 dispatch build/release。
- 因此不能把“直接推主分支”视为仅保存源码，也不能未经批准运行发布工作流。

## 独立复审补丁（冻结基线 b678cdc 之后）

- 复跑基线 81 个测试通过；新增回归先红后绿，现为 82 个测试。
- 修正上节两项已知残余：只在 `menu_common.cpp` 扫描 `joined` 初始化表达式和
  `SliderFloat` 的格式参数，补入 ` or ` 与两种 `of screen` 格式（共 3 条）。
  纯数字/百分比/px 技术格式不入词库；已有翻译不变。
- `join_with` 仍持有 `std::string` 分隔符；只替换内部字面量为稳定 `Loc::T` 指针，
  不把临时字符串的 `c_str()` 交给惰性 range。FSR/DLSS/XeSS 技术名与 Keybind 构造值不变。
- 检查运行时格式使用 `Loc::F`/`std::vformat`，无 `std::format(Loc::T(...))`；
  tooltip 注入顺序、NR 诊断持有字符串生命周期、相邻字面量和 toast 内容字段回归均通过。
- 独立按实际源文件调用参数再扫原始英文（排除注释与 vendored imgui），
  `menu_common.cpp` / `DlssNr_Menu.cpp` 剩余直接 UI 字面量为保留的技术缩写；
  这不是对游戏运行时动态字符串或全部第三方组件的穷尽证明。
- 两通道 1039 active、missing/stale=0，原译文零改；新补丁只加 3 条 reviewed。
- Windows 编译与游戏内验收仍待执行，不以扫描覆盖率替代其结果。
- 复核发现 `release.yml` 还会直接响应 main/master 的 `Localization/zh-CN.json` push；
  因此仅允许维护分支 + draft PR 的只读权限 build/localization-check 路线，不合并或发布。
