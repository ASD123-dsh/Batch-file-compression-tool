# 批量文件压缩工具 v2.0

该项目是一个模块化的批量图片/视频压缩工具，提供桌面 GUI（Tkinter）与可选 Web 服务（Flask）。支持暂停/恢复、断点续传、压缩预览与历史记录，并内置 FFmpeg 自动检测与（Windows）下载。

## 主要特性
- 支持图片与视频批量压缩，自动创建目标目录结构
- 暂停/恢复与断点续传，异常退出后可继续未完成任务
- 压缩预览（单文件），显示压缩率与大小对比
- GPU 加速：AMD（AMF）与 Nvidia（NVENC），失败自动回退 CPU
- 编码器与容器兼容性校验（WebM 强制 CPU 编码）
- 自动保存历史记录（JSON）
- Windows 平台自动检测/下载 FFmpeg

## 架构与模块职责
- config_manager.py：配置加载/保存/默认值与校验
- path_utils.py：统一路径（开发/打包态），提供 config/bin/log/history 目录
- file_processor.py：路径规范化、权限与空间检查、大小估算、显示格式化
- file_info.py：紧凑数据结构（__slots__），延迟计算源/目标路径
- image_compressor.py：图片压缩（Pillow），失败回退复制
- video_compressor.py：视频压缩（FFmpeg，CPU/AMF/NVENC），失败自动回退
- encoder_compatibility.py：编码器-容器-音频兼容表与默认选择、模式限制
- compression_history.py：历史记录存取与数量限制
- ffmpeg_manager.py：FFmpeg 检测、断点续传式下载与解压清理（Windows）
- web_server.py（可选）：Flask 路由（单文件/批量上传压缩）、Web 配置与预设
- compress_tool.py：主程序 UI、事件绑定、线程池压缩与进度/状态更新

## 目录结构（根目录）
```
.
├── compress_tool.py
├── config_manager.py
├── file_processor.py
├── file_info.py
├── image_compressor.py
├── video_compressor.py
├── encoder_compatibility.py
├── compression_history.py
├── ffmpeg_manager.py
├── web/
│   ├── static/ (JS/CSS)
│   └── templates/ (HTML)
├── FileCompressor.spec
├── FileCompressorLite.spec
├── requirements.txt
├── README.md
├── picture.ico
└── （运行时生成）bin/、history/、logs/、checkpoint.json
```

## 支持格式与编码说明
- 图片：JPG/JPEG/PNG/GIF/BMP/TIFF/WEBP（按 JPEG 质量/尺寸压缩）
- 视频容器：MP4/MKV/MOV/AVI/WEBM 等
- 视频编码：CPU（libx264/x265/VP8/VP9/AV1）与 GPU（AMF/NVENC）
- 兼容性规则：如 WEBM（.webm）仅支持 CPU；自动选择兼容音频编码（AAC/MP3/Opus/Vorbis）

## 安装与运行
- 环境要求：Python 3.7+；Tkinter（标准库）；Pillow（>=9.0.0）
- 可选：Flask、flask-cors（Web 服务）；opencv-python（视频预览）
- 安装依赖：
  ```
  pip install -r requirements.txt
  ```
- 桌面运行：
  ```
  python compress_tool.py
  ```
- FFmpeg（Windows）：
  - 程序启动自动检测；缺失时可自动下载至 bin/ 并验证
  - 其他平台请手动安装并加入 PATH 或配置 ffmpeg_path

## 基本使用
- 选择源/目标文件夹，设置“照片质量”“视频 CRF/预设”“编码模式（CPU/AMD/Nvidia）”
- 开始压缩（支持暂停/恢复/停止），压缩进度与剩余时间实时更新
- 断点续传：任务中断后自动保存 checkpoint.json；下次启动可选择继续
- 历史记录：自动保存统计信息，可查看/清空
- 压缩预览：选中单个文件进行预览

## 快捷键
- Ctrl+O 选择源文件夹；Ctrl+D 选择目标文件夹；Ctrl+E 打开输出
- Ctrl+S 保存设置；F5 刷新文件列表
- Ctrl+R 开始压缩；Ctrl+P 暂停；Ctrl+U 恢复；Ctrl+T 停止；Ctrl+Q 退出

## 配置说明（config.ini 示例）
```
[General]
ffmpeg_path = bin\ffmpeg.exe
photo_quality = 85
video_crf = 23
video_preset = medium
max_photo_width = 2000
max_photo_height = 2000
resolution_preset = 自定义
output_folder = compressed
use_gpu = cpu
video_container = .mp4
video_encoder = libx264
cpu_encoder = libx264
audio_encoder = aac
video_bitrate = 5000k

[Paths]
source_dir =
target_dir =
```
- 说明：WEBM（.webm）容器强制 CPU；GPU 模式下使用比特率参数，CPU 模式下使用 CRF
- 配置由程序启动时自动加载/保存；Web 模式使用 web_config.ini

## 打包构建（PyInstaller）
- 完整版（含 Web 资源）：
  ```
  pyinstaller FileCompressor.spec
  ```
  - 生成 dist/FileCompressor/FileCompressor.exe
- 轻量版（去除 Web 依赖）：
  ```
  pyinstaller FileCompressorLite.spec
  ```
  - 生成 dist/FileCompressorLite/FileCompressorLite.exe
- 应用图标：两个版本均使用 picture.ico（已在 .spec 配置）

## 注意事项
- FFmpeg 路径与可执行权限；GPU 使用需安装对应驱动
- 运行时生成与缓存目录：bin/、history/、logs/、checkpoint.json、web/uploads/、web/outputs/
- .gitignore 已忽略构建产物与运行时文件，确保提交干净

## 许可证
Copyright © 2024-2025 批量文件压缩工具
本软件仅供个人学习和非商业用途使用。

