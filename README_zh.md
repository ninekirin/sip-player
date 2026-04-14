# SIP 播放器

基于 SIP 的音乐播放器，支持 DTMF IVR 控制。自动接听来电并向呼叫方播放音频曲目。可通过 DTMF 音频或 GUI 控制播放。

## 功能特性

- **SIP 注册**: 可注册到任意 SIP 服务器
- **自动接听**: 自动接听来电
- **音频播放**: 向 SIP 通话播放 WAV 音频文件
- **DTMF 控制**: 通过 DTMF 音频控制播放 (1/2/3/4)
- **多会话**: 支持多个并发通话
- **双语界面**: 简体中文和英文界面
- **导入功能**: 通过 ffmpeg 将 MP3/M4A/FLAC 转换为 WAV

## 系统要求

- **Python**: 3.12 或更高版本
- **PJSIP**: 2.16+ (带 pjsua2 Python 绑定)
- **tkinter**: GUI 框架
- **ffmpeg**: 用于音频格式转换（可选，用于导入功能）

## 平台配置

选择您的平台查看详细配置说明：

- [Windows](#windows-配置)
- [macOS](#macos-配置)
- [Linux](#linux-配置)

---

## Windows 配置

### 步骤 1: 安装 Python

1. 从 [python.org](https://www.python.org/downloads/) 下载 Python 3.12+
2. 安装时**勾选 "Add Python to PATH"**
3. 验证安装：
   ```cmd
   python --version
   ```

### 步骤 2: 安装 tkinter

Windows 版 Python 已包含 tkinter。验证是否可用：
```cmd
python -c "import tkinter; print('tkinter OK')"
```

如果报错，重新安装 Python 并确保选中 tcl/tk 组件。

### 步骤 3: 安装构建工具

下载并安装 [Visual Studio Community](https://visualstudio.microsoft.com/zh-hans/downloads/)：
- 安装时选择 **"使用 C++ 的桌面开发"**
- 或安装 [Visual Studio 构建工具](https://visualstudio.microsoft.com/zh-hans/downloads/#build-tools-for-visual-studio-2022)

### 步骤 4: 安装 SWIG

1. 从 [swig.org](http://www.swig.org/download.html) 下载 SWIG
2. 解压到无空格路径（如 `C:\swigwin`）
3. 添加 SWIG 到 PATH：
   - 按 Win+R，输入 `sysdm.cpl`
   - 进入 **高级** → **环境变量**
   - 将 `C:\swigwin` 添加到 `Path`

验证：
```cmd
swig -version
```

### 步骤 5: 编译 PJSIP

1. 从 [pjsip.org](https://pjsip.org/download.htm) 或 GitHub 下载 PJSIP：
   ```cmd
   git clone https://github.com/pjsip/pjproject.git
   cd pjproject
   ```

2. 配置并构建：
   ```cmd
   cd pjproject
   python ./configure.py
   ```

3. 在 Visual Studio 中打开生成的解决方案：
   - **Visual Studio 2022**: `pjsip-apps\build\vs2022\pjsua_vc2022.sln`
   - 以 **Release** 模式构建整个解决方案

4. 构建 SWIG Python 绑定：
   ```cmd
   cd pjsip-apps\src\swig
   python setup.py build
   python setup.py install
   ```

### 步骤 6: 安装 ffmpeg（可选）

用于音频导入功能：
1. 从 [ffmpeg.org](https://ffmpeg.org/download.html#build-windows) 下载
2. 解压并将 `bin` 文件夹添加到 PATH

### 步骤 7: 安装 sip-player

```cmd
cd sip-player
pip install -e .
```

---

## macOS 配置

### 步骤 1: 安装 Python

使用 Homebrew：
```bash
brew install python@3.12
```

或从 [python.org](https://www.python.org/downloads/) 下载。

验证：
```bash
python3 --version
```

### 步骤 2: 安装 tkinter

**Homebrew 安装的 Python：**
```bash
brew install python-tk@3.12
```

**官方安装包：**
tkinter 已包含。验证：
```bash
python3 -c "import tkinter; print('tkinter OK')"
```

如果使用 pyenv，需重新安装带 tcl-tk 支持的版本：
```bash
brew install tcl-tk
export LDFLAGS="-L$(brew --prefix tcl-tk)/lib"
export CPPFLAGS="-I$(brew --prefix tcl-tk)/include"
export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"
pyenv install 3.12.0
```

### 步骤 3: 安装依赖

```bash
brew install swig ffmpeg
```

### 步骤 4: 编译 PJSIP

```bash
# 克隆 PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject

# 配置（添加 -fPIC 用于共享库）
./configure CFLAGS="-fPIC"

# 编译（5-10 分钟）
make dep && make

# 编译 SWIG Python 绑定
cd pjsip-apps/src/swig
make

# 安装 pjsua2 模块
cd python
python3 setup.py install
```

验证安装：
```bash
python3 -c "import pjsua2; print('pjsua2 OK')"
```

### 步骤 5: 安装 sip-player

```bash
cd sip-player
pip3 install -e .
```

---

## Linux 配置

已在 Ubuntu/Debian 和 Fedora/RHEL 上测试。

### Ubuntu/Debian

```bash
# 安装 Python、tkinter 和构建工具
sudo apt update
sudo apt install -y python3 python3-tk python3-dev build-essential swig ffmpeg

# 安装 PJSIP 依赖
sudo apt install -y libssl-dev libsrtp2-dev libopus-dev libspeex-dev libgsm1-dev

# 克隆并编译 PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject
./configure CFLAGS="-fPIC"
make dep && make

# 编译 SWIG Python 绑定
cd pjsip-apps/src/swig
make
cd python
python3 setup.py install --user

# 验证
python3 -c "import pjsua2; print('pjsua2 OK')"
```

### Fedora/RHEL

```bash
# 安装依赖
sudo dnf install -y python3 python3-tkinter python3-devel gcc gcc-c++ make swig ffmpeg openssl-devel opus-devel speex-devel gsm-devel

# 克隆并编译 PJSIP
git clone https://github.com/pjsip/pjproject.git
cd pjproject
./configure CFLAGS="-fPIC"
make dep && make

# 编译 SWIG Python 绑定
cd pjsip-apps/src/swig
make
cd python
python3 setup.py install --user
```

### 安装 sip-player

```bash
cd sip-player
pip3 install -e .
```

---

## 运行程序

### GUI 模式

```bash
# Windows
python -m src

# macOS/Linux
python3 -m src
```

或使用安装的命令：
```bash
sip-player
```

### DTMF 控制

通话中，使用 DTMF 音频控制播放：

| 按键 | 功能 |
|-----|------|
| 1 | 下一首 |
| 2 | 播放/暂停 |
| 3 | 切换播放模式 |
| 4 | 上一首 |

### 播放模式

1. **顺序播放** - 按顺序播放，播完停止
2. **列表循环** - 循环播放所有曲目
3. **单曲循环** - 重复当前曲目
4. **随机播放** - 随机打乱播放

---

## 配置文件

设置自动保存到：
- **Windows**: `%APPDATA%\sip_player\settings.json`
- **macOS**: `~/Library/Application Support/sip_player/settings.json`
- **Linux**: `~/.config/sip_player/settings.json`

导入的音频文件存储在：
- **Windows**: `%LOCALAPPDATA%\sip_player\imported_tracks\`
- **macOS**: `~/Library/Application Support/sip_player/imported_tracks/`
- **Linux**: `~/.local/share/sip_player/imported_tracks/`

---

## 常见问题

### PJSIP 安装问题

**"build.mak: No such file or directory"**
- 确保在 pjproject 根目录执行了 `./configure` 和 `make dep && make`

**"pjsua2_wrap.cpp: No such file or directory"**
- 在 `pjsip-apps/src/swig` 目录下执行 `make`

**"Cannot determine JDK include path"**
- 如只需 Python 绑定可忽略此错误

### macOS: "tkinter 未找到"

如果使用 pyenv，需重新安装带 tcl-tk 支持的 Python（见步骤 2）。

### Windows: 编译错误

- 确保已安装带 C++ 工具的 Visual Studio
- 从 **x64 Native Tools 命令提示符** 运行命令
- 验证 SWIG 已在 PATH 中

---

## 许可证

MIT License

## 参考资料

- [PJSIP 官方文档](https://docs.pjsip.org/)
- [PJSIP GitHub](https://github.com/pjsip/pjproject)
- [SWIG 官方文档](https://www.swig.org/doc.html)
