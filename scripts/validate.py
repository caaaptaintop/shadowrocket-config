#!/usr/bin/env python3
"""Validate the publishable config; domain probes are offline approximations, not SR runtime tests."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fnmatch
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import ssl
import subprocess
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OWN = "https://raw.githubusercontent.com/caaaptaintop/shadowrocket-config/main/"
UPSTREAM = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/"
BUILTINS = {"DIRECT", "REJECT", "PROXY"}
TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
         "IP-CIDR", "IP-CIDR6", "IP-ASN", "USER-AGENT", "URL-REGEX"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def meaningful(text):
    return [s.strip() for s in text.splitlines() if s.strip() and not s.lstrip().startswith("#")]


def sections(text):
    result, current = {}, None
    for line in meaningful(text):
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            require(current not in result, f"重复配置段：{current}")
            result[current] = []
        else:
            require(current is not None, "配置段外存在内容")
            result[current].append(line)
    return result


def assignment(lines):
    result = {}
    for line in lines:
        require("=" in line, "配置键缺少等号")
        key, value = (s.strip() for s in line.split("=", 1))
        require(key not in result, f"重复键：{key}")
        result[key] = value
    return result


def parse_rules(text, domain_set=False):
    result = []
    for line in meaningful(text):
        if domain_set:
            domain = line.lstrip(".")
            require(bool(re.fullmatch(r"[a-zA-Z0-9_.*-]+", domain)), "DOMAIN-SET 域名格式错误")
            result.append(("DOMAIN-SUFFIX" if line.startswith(".") else "DOMAIN", domain))
        else:
            bits = line.split(",")
            require(len(bits) >= 2 and bits[0] in TYPES, "规则集含不支持的格式")
            require(len(bits) == 2 or (len(bits) == 3 and bits[2] == "no-resolve"),
                    "规则集混入策略列或无效参数")
            if bits[0] in {"IP-CIDR", "IP-CIDR6"}:
                ipaddress.ip_network(bits[1], strict=False)
            result.append((bits[0], bits[1]))
    require(bool(result), "规则文件为空")
    return result


def scan_public():
    if (ROOT / ".git").exists():
        tracked = subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=ROOT, text=True).split("\0")
        require(not any(p.startswith("local/") or p.endswith((".db", ".zip", ".p12", ".pem", ".key"))
                        for p in tracked), "Git 中包含本机数据或证书文件")
    files = [ROOT / "Shadowrocket.conf", *sorted((ROOT / "rules").glob("*.list"))]
    for path in files:
        text = path.read_text()
        # Print only the filename and category if validation fails, never the value.
        require(not re.search(r"(?i)(password|token|private[-_]?key|p12|authorization)\s*[:=]", text),
                f"{path.name} 含凭据字段")
        require(not re.search(r"(?i)(ss|ssr|vmess|vless|trojan|hysteria2?)://", text),
                f"{path.name} 含节点 URI")
        require(not re.search(r"(?i)\bpolicy-path\s*=", text),
                f"{path.name} 含本机订阅绑定")


def inspect(config):
    parsed = sections(config)
    require(set(parsed) == {"General", "Proxy Group", "Rule"}, "公开配置只允许通用参数、分组和规则")
    general = assignment(parsed["General"])
    require(general.get("update-url") == OWN + "Shadowrocket.conf", "配置更新地址未指向本人仓库")
    require(general.get("ipv6") == "false" and general.get("dns-direct-system") == "true",
            "已接受的 IPv6/DNS 设置被改变")
    groups = assignment(parsed["Proxy Group"])
    for name, value in groups.items():
        parts = value.split(",")
        require(parts[0] == "select", f"{name} 必须保持手动选择")
        members = [s for s in parts[1:] if "=" not in s]
        require(all(s in groups or s in BUILTINS for s in members), f"{name} 引用了未定义策略")
        selected = next((s.split("=", 1)[1] for s in parts if s.startswith("policy-select-name=")), None)
        require(selected is None or selected in members, f"{name} 默认选项不存在")
        regex = next((s.split("=", 1)[1] for s in parts if s.startswith("policy-regex-filter=")), None)
        if regex:
            re.compile(regex)
    for name in ("OpenAI", "Claude", "Gemini"):
        require("policy-select-name=US" in groups.get(name, ""), f"{name} 默认出口必须是 US")
    rules = [s.split(",") for s in parsed["Rule"]]
    expected = [["RULE-SET", OWN + "rules/CustomDirect.list", "DIRECT"],
                ["RULE-SET", OWN + "rules/OpenAI.list", "OpenAI"],
                ["RULE-SET", OWN + "rules/Claude.list", "Claude"],
                ["RULE-SET", OWN + "rules/Gemini.list", "Gemini"]]
    require(rules[:4] == expected, "自定义直连/AI 规则必须位于上游之前")
    require(rules[-2:] == [["GEOIP", "CN", "DIRECT"], ["FINAL", "Final"]], "兜底顺序错误")
    urls = []
    for bits in rules:
        require(len(bits) in (2, 3), "主规则列数错误")
        policy = bits[-1]
        require(policy in groups or policy in BUILTINS, "规则引用未定义策略")
        if bits[0] in {"RULE-SET", "DOMAIN-SET"}:
            url = bits[1]
            parsed_url = urlparse(url)
            require(url.startswith((OWN, UPSTREAM)) and parsed_url.scheme == "https" and
                    not parsed_url.query and not parsed_url.fragment and not parsed_url.username,
                    "远程规则地址越界或含认证参数")
            require(".." not in parsed_url.path.split("/"), "规则地址路径越界")
            urls.append((url, bits[0] == "DOMAIN-SET", policy))
        else:
            require(bits[0] in {"GEOIP", "FINAL"}, "主配置含非预期规则")
    require(len(urls) == len({u[0] for u in urls}), "重复远程规则引用")
    for name, policy in (("Apple", "Apple"), ("China", "DIRECT"), ("Global", "Proxies")):
        prefix = UPSTREAM + name + "/" + name
        require((prefix + ".list", False, policy) in urls and
                (prefix + "_Domain.list", True, policy) in urls,
                f"{name} 缺少配套 DOMAIN-SET 或策略不一致")
    return groups, rules, urls


def source_content(url, online, cached):
    if url.startswith(OWN):
        path = ROOT / url[len(OWN):]
        require(path.is_file(), "本人仓库引用的规则文件不存在")
        return path.read_text()
    cache = ROOT / "local" / "upstream" / (hashlib.sha256(url.encode()).hexdigest() + ".list")
    if online:
        request = Request(url, headers={"User-Agent": "shadowrocket-config-validator"})
        ca_paths = ssl.get_default_verify_paths()
        context = ssl.create_default_context()
        if ca_paths.cafile is None and ca_paths.capath is None:
            try:
                import certifi  # Optional: existing macOS Python installation lacks its default CA file.
            except ImportError:
                pass
            else:
                context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=25, context=context) as response:
            require(response.status == 200 and response.geturl() == url, "上游资源响应异常")
            raw = response.read(8 * 1024 * 1024 + 1)
        require(len(raw) <= 8 * 1024 * 1024, "上游规则超出大小限制")
        text = raw.decode("utf-8-sig")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text)
        return text
    if cached:
        require(cache.is_file(), "缺少已核验的上游缓存，请先运行 --online")
        return cache.read_text()
    return None


def matches(kind, value, domain):
    if kind == "DOMAIN":
        return domain == value.lower()
    if kind == "DOMAIN-SUFFIX":
        return domain == value.lower() or domain.endswith("." + value.lower())
    if kind == "DOMAIN-KEYWORD":
        return value.lower() in domain
    if kind == "DOMAIN-WILDCARD":
        return fnmatch.fnmatchcase(domain, value.lower())
    return False  # IP, USER-AGENT and URL matching require real SR traffic.


def route(domain, refs, contents):
    for url, is_domain, policy in refs:
        entries = contents.get(url)
        if entries and any(matches(k, v, domain) for k, v in entries):
            return policy
    return "Final"


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--online", action="store_true")
    mode.add_argument("--cached", action="store_true")
    args = parser.parse_args()
    scan_public()
    config = (ROOT / "Shadowrocket.conf").read_text()
    groups, rules, refs = inspect(config)
    loaded, evidence = {}, []

    def load(ref):
        url, is_domain, policy = ref
        text = source_content(url, args.online, args.cached)
        if text is None:
            return url, None, None
        entries = parse_rules(text, is_domain)
        stamp = re.search(r"^# UPDATED:\s*(.+)$", text, re.M)
        return url, entries, {"url": url, "rules": len(entries), "policy": policy,
                              "updated": stamp.group(1) if stamp else None,
                              "sha256": hashlib.sha256(text.encode()).hexdigest()}

    with ThreadPoolExecutor(max_workers=6) as pool:
        for url, entries, item in pool.map(load, refs):
            if entries is not None:
                loaded[url] = entries
                evidence.append(item)
    cases = {"proma.cool": "DIRECT", "api.qrserver.com": "DIRECT", "kdocs.cn": "DIRECT",
             "drive.wps.cn": "DIRECT", "wps365cdn.com": "DIRECT", "kugou.com": "DIRECT",
             "www.kugou.com": "DIRECT", "api.openai.com": "OpenAI", "chatgpt.com": "OpenAI",
             "files.oaiusercontent.com": "OpenAI", "cdn.oaistatic.com": "OpenAI",
             "claude.ai": "Claude", "api.anthropic.com": "Claude",
             "gemini.google.com": "Gemini", "aistudio.google.com": "Gemini",
             "generativelanguage.googleapis.com": "Gemini"}
    if args.online or args.cached:
        cases.update({"www.youtube.com": "YouTube", "github.com": "GitHub",
                      "raw.githubusercontent.com": "GitHub", "www.bilibili.com": "Bilibili",
                      "www.google.com": "Google", "outlook.com": "Microsoft",
                      "www.apple.com": "Apple", "www.baidu.com": "DIRECT",
                      "www.wikipedia.org": "Proxies", "unlisted-example.invalid": "Final"})
    probes = []
    for domain, expected in cases.items():
        actual = route(domain, refs, loaded)
        require(actual == expected, f"分流用例失败：{domain}，期望 {expected}，得到 {actual}")
        probes.append({"domain": domain, "policy": actual})
    result = {"mode": "online" if args.online else "cached" if args.cached else "offline",
              "groups": len(groups), "references": len(refs), "loaded_sources": len(loaded),
              "probes": probes, "sources": evidence,
              "scope": "配置静态校验和域名规则近似匹配；不代表 SR 编译、IP/UA/URL 或联网验收"}
    local = ROOT / "local"
    local.mkdir(exist_ok=True)
    (local / ("validation-" + result["mode"] + ".json")).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS: {len(groups)} 分组，{len(refs)} 规则引用，{len(probes)} 域名用例；模式 {result['mode']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # No response body or private configuration is included in errors.
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
