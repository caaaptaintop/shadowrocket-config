# Shadowrocket 配置

状态：**已发布，并于 2026-10-08 在现有设备启用。**

自己的 GitHub 仓库保存主配置和自定义规则，通用规则直接引用 blackmatrix7 的 Shadowrocket 格式。节点订阅仍在 SR 首页管理。

## 当前分流

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

仓库：[caaaptaintop/shadowrocket-config](https://github.com/caaaptaintop/shadowrocket-config)，公开，仅保存无凭据的配置和规则。

换设备使用的完整主配置地址：

```text
https://raw.githubusercontent.com/caaaptaintop/shadowrocket-config/main/Shadowrocket.conf
```

现有设备正在使用 **`本机专用.conf`**，它保存 24 个交互分组、原来的五个地区组订阅绑定、具体节点选择和三条 Hosts 映射；通过 `include = Rules.conf` 加载公共规则。这份本机文件和一致性配置快照只在本机保存，不提交 GitHub。

SR 中的 **`Rules.conf`** 来自以下地址。它只包含通用设置和规则，不含分组，用于避免更新时同名分组覆盖本机选择；请通过本机入口使用它。

```text
https://raw.githubusercontent.com/caaaptaintop/shadowrocket-config/main/Rules.conf
```

已经实测：更新 `Rules.conf` 后重新使用 `本机专用.conf`，五个地区原节点选择、三个 AI 的美国出口和三条 Hosts 均保留。单独启用完整主配置时使用其默认分组，不会带回本机附加信息。

换设备可直接恢复 GitHub 上的主配置和自定义规则，再添加节点订阅。具体节点选择、Hosts 和应用设置属于本机附加信息，不能仅靠公开仓库恢复。

## 日常维护与更新

日常只需记住：**节点在首页更新；规则更新 `Rules.conf`，然后使用 `本机专用.conf`。**

1. 长期增加直连或 AI 规则，修改 `rules/` 下对应文件并提交 GitHub；通用规则直接引用上游，个人规则放在它们之前，不需要 Fork 上游仓库。
2. 修改通用设置或主配置中的规则引用后，运行 `python3 scripts/build_rules.py` 生成配套 `Rules.conf`，验证后一起提交。
3. 当前设备更新：在 SR 配置页点 `Rules.conf` → **更新**；再点 `本机专用.conf` → **使用配置**。本机入口没有公共更新地址，避免用公共文件覆盖本机分组和 Hosts。
4. 分组结构需要长期修改时，同时修改主配置和本机入口，并保留原订阅绑定及选择。SR 界面修改不会自动上传 GitHub；公开配置或规则文件中的长期改动需要回写仓库。
5. 自定义直连与 AI 规则位于上游规则之前。模块规则会优先于主配置，不启用大范围 DIRECT/PROXY 模块覆盖这些分组。

仓库 CI 在提交或 PR 时检查配置，没有定时同步任务。现有 SR 的“打开应用时更新订阅”和“自动更新订阅”设置均已开启；后台实际触发及无人值守规则更新尚未验证。

## 验证

```bash
python3 scripts/build_rules.py
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
