#!/usr/bin/env bash
# 外刊精读讲义技能 · Linux 依赖安装（Ubuntu 22.04 / Debian 12）
#
# 做四件事：
#   ① 补齐 python3-pip      ② 装中文字体（不装会让讲义中文变方框）
#   ③ 装一个 Chromium 系浏览器  ④ 装 Python 依赖 pymupdf，并做自检
#
# 幂等，可重复运行。用法：  bash assets/setup_linux.sh
# 指定解释器：            PYTHON=/usr/bin/python3.11 bash assets/setup_linux.sh
set -euo pipefail

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  command -v sudo >/dev/null 2>&1 || die "需要 root 权限或 sudo 来安装系统包"
  SUDO="sudo"
fi

[ -r /etc/os-release ] || die "无法识别发行版：缺少 /etc/os-release"
# shellcheck disable=SC1091
. /etc/os-release
info "发行版: ${PRETTY_NAME:-unknown} (ID=${ID:-?} VERSION_ID=${VERSION_ID:-?})"

apt_install() {
  info "apt install: $*"
  $SUDO apt-get update -qq
  $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
}

# ---------- ① python3-pip ----------
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || die "找不到 $PY，请先装 Python 3.10+"

if ! "$PY" -m pip --version >/dev/null 2>&1; then
  info "未检测到 pip，安装 python3-pip / python3-venv"
  apt_install python3-pip python3-venv
else
  info "pip 已存在，跳过"
fi

# ---------- ② 中文字体 ----------
if command -v fc-list >/dev/null 2>&1 \
   && fc-list 2>/dev/null | grep -qiE 'noto.*cjk|wqy|source han'; then
  info "中文字体已存在，跳过"
else
  info "安装中文字体 fonts-noto-cjk（讲义中文依赖它，否则渲染成方框）"
  apt_install fonts-noto-cjk
fi

# ---------- ③ 浏览器 ----------
have_browser() {
  local b
  for b in chromium chromium-browser google-chrome google-chrome-stable microsoft-edge; do
    command -v "$b" >/dev/null 2>&1 && return 0
  done
  return 1
}

if have_browser; then
  info "已检测到 Chromium 系浏览器，跳过安装"
else
  case "${ID:-}" in
    debian)
      info "Debian：尝试用系统包 chromium"
      apt_install chromium || warn "apt 安装 chromium 失败，稍后回退到 Playwright"
      ;;
    ubuntu)
      # Ubuntu 22.04 的 chromium-browser 是 snap 包装器，在容器 / 无 snapd 的环境里不可用，
      # 所以这里不折腾 apt，直接走 Playwright 自带 Chromium。
      warn "Ubuntu 的 chromium 走 snap 通道，容器环境常常装不上，改用 Playwright 自带 Chromium"
      ;;
    *)
      warn "未知发行版 ${ID:-?}，跳过系统包，直接尝试 Playwright"
      ;;
  esac
fi

if ! have_browser; then
  info "安装 Playwright 自带 Chromium（不依赖发行版打包，路径固定可预测）"
  "$PY" -m pip install --user --quiet playwright \
    || die "pip 安装 playwright 失败，请检查网络或 pip 源"
  "$PY" -m playwright install --with-deps chromium \
    || die "playwright install 失败（--with-deps 需要 sudo 权限装系统库）"
fi

# ---------- ④ Python 依赖 ----------
info "安装 pymupdf"
"$PY" -m pip install --user --quiet pymupdf || warn "pymupdf 安装失败，请手动 pip install pymupdf"

# ---------- 自检 ----------
info "自检"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PY" - <<'PYEOF' || die "自检失败：渲染脚本找不到可用浏览器（可设 LECTURE_BROWSER 手动指定）"
import render_pdf
print("  浏览器:", render_pdf.find_browser())
import pymupdf
print("  pymupdf:", pymupdf.__doc__.strip().splitlines()[0] if pymupdf.__doc__ else "ok")
PYEOF

if command -v fc-list >/dev/null 2>&1 && ! fc-list 2>/dev/null | grep -qiE 'noto.*cjk|wqy|source han'; then
  warn "仍未检测到 CJK 字体，讲义中文可能显示为方框"
else
  info "中文字体 OK"
fi

cat <<'EOF'

完成。试渲染一份讲义：
  python3 assets/render_pdf.py src/<文章名>.md output/<输出名>.pdf --preview

EOF
