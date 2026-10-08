# Shadowrocket 配置维护

- 先读 README.md、docs/当前状态.md 和本次实际改动文件。
- GitHub 是主配置和自定义规则的真源；SR 本地修改需先回写仓库再更新。
- 仅发布 Shadowrocket.conf、Rules.conf、rules/、scripts/、.github/、README.md、LICENSE 及项目说明。
- local/ 含配置快照、订阅分组选择和 Hosts，禁止提交、公开或回显秘密正文。
- 节点订阅、密码、证书、代理共享端口和系统代理在本机维护。
- 优先保留已接受的直连例外、分组选择、DNS 和 IPv6 设置。
- 验证：python3 scripts/validate.py；改动上游引用时再加 --online。
- 修改主配置后运行 python3 scripts/build_rules.py；Rules.conf 是不含分组的生成文件。本机入口含完整交互分组并 include=Rules.conf，修改分组时同步本机入口并保留已有选择。
- 发布前展示本次变化；确认后只发布已展示范围，并验证实际 SR 规则和联网。
