# Shadowrocket 配置

状态：**发布接入中，用户已确认本地预览。** 创建日期：2026-10-08。

自己的 GitHub 仓库保存主配置和自定义规则，通用规则直接引用 blackmatrix7 的 Shadowrocket 格式。节点订阅仍在 SR 首页管理。

## 配置预览

| 流量 | 默认策略 | 维护位置 |
| --- | --- | --- |
| Proma、二维码 API、WPS/金山文档、酷狗 | DIRECT | rules/CustomDirect.list |
| OpenAI / ChatGPT | OpenAI → US，手动选择 | rules/OpenAI.list |
| Claude / Anthropic API | Claude → US，手动选择 | rules/Claude.list |
| Gemini 网页 / API / AI Studio | Gemini → US，手动选择 | rules/Gemini.list |
| YouTube、微软服务 | 各自分组 → US | 上游专项规则 |
| Bilibili、国内 Steam CDN | DIRECT | 上游专项规则 |
| GitHub、Google、其他媒体、Apple | 各自分组 → Proxies → US | 上游专项规则 |
| 国内服务 / 中国 IP | DIRECT | China 域名及规则集 / GEOIP |
| 其余流量 | Final → Proxies → US | 主配置兜底 |

Apple 的默认代理策略沿用现有设置。全部分组使用手动选择；三个 AI 服务可分别调整出口。

保留现用配置全部 13 项 General 参数，包括 DNS、IPv6 关闭、局域网旁路和 UDP 不支持时拒绝；端口、系统代理和订阅在应用内管理。

## 仓库与导入

发布目标：`caaaptaintop/shadowrocket-config`，公开，仅保存无凭据的配置和规则。

发布后主配置地址为：

```text
https://raw.githubusercontent.com/caaaptaintop/shadowrocket-config/main/Shadowrocket.conf
```

主配置地址由发布流程核验后导入，接入结果见 `docs/当前状态.md`。

正式接入由 Codex 在预览确认后执行：发布并核验 Raw 内容；在 SR 中添加远程主配置；核对地区组和默认节点；导入本机附加配置后启用；测试指定域名策略与实际联网。

现有设备还需要 `local/本机专用.conf`：它包含主配置，保留原来的五个地区组订阅绑定、具体节点选择和三条 Hosts 映射。此文件和一致性配置快照只在本机保存，不提交 GitHub。SR 主配置名称须为 `Shadowrocket.conf`，附加配置通过 `include = Shadowrocket.conf` 引用它。真实包含配置行为待 SR 导入验证。

换设备可直接恢复 GitHub 上的主配置和自定义规则，再添加节点订阅。具体节点选择、Hosts 和应用设置属于本机附加信息，不能仅靠公开仓库恢复。

## 日常维护与更新

1. 长期调整先修改本仓库主配置或规则文件，验证后提交 GitHub。
2. SR 的“更新配置”从自己的 GitHub 拉取主配置；SR 的使用/编译配置功能可重新拉取远程规则集。
3. 主配置更新不会改写 GitHub 中的自定义规则；上游通用规则由上游维护，通过规则集引用拉取，不需要 Fork 整个规则仓库。
4. SR 界面临时修改不会自动上传 GitHub。需要长期保留时，先导出、回写并提交，再更新 SR，否则远程配置会覆盖本地修改。
5. 自定义直连与 AI 规则位于上游规则之前。模块规则会优先于主配置，不启用大范围 DIRECT/PROXY 模块覆盖这些分组。

仓库 CI 只在提交或 PR 时运行静态检查，没有定时同步任务。SR 原生后台更新的设置和实际运行均待接入阶段核验；目前不能称自动更新已运行。

## 验证

```bash
python3 scripts/validate.py
python3 scripts/validate.py --online
```

`--online` 通过 HTTPS 校验 21 个上游资源并保存本机缓存；之后可用 `--cached` 复用该批证据。默认模式在本地校验自定义规则、分组、更新地址、配套域名文件、公开文件边界和关键域名。无需安装依赖；Mac Python 缺少默认 CA 文件时可使用已安装的 certifi，TLS 验证保持开启。

检查结果见 [验证结果](docs/验证结果.md)。此验证器只近似匹配域名规则，不能代替 SR 编译、IP/UA/URL 规则测试、VPN 连接、模型登录或联网测试。

## 回滚

旧 `Clash迁移到Shadowrocket.conf` 保留原状。新配置启用后如出现异常，切回旧配置即可；`local/迁移前配置.db` 为 SQLite 一致性快照，可供本机恢复。不要将快照或本机附加配置上传仓库。

## 来源

- [LOWERTOP 配置说明](https://github.com/LOWERTOP/Shadowrocket/blob/main/lazy_group.conf)：SR 分组、更新和包含配置语法参考。
- [blackmatrix7 Shadowrocket 规则](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket)：通用分流源，只引用远程资源，不复制进仓库。
- [China 规则说明](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket/China)：明确要求 `.list` 与 `_Domain.list` 搭配；Apple、Global 同样核对了配套文件。
- [OpenAI 网络建议](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)：ChatGPT 核心域名依据。
- [Gemini API 端点](https://ai.google.dev/api/all-methods)：`generativelanguage.googleapis.com`。

本仓库自有配置和脚本采用 MIT；上游远程资源遵循各自许可证，不适用本仓库许可证。AI 域名列表由本人仓库维护，不宣称自动同步官方域名变化。
