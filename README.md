# 统计次数

## 使用说明
支持Windows10/11系统，双击exe文件即可使用，无需安装。
1. 下载
    * release中[下载](https://github.com/Shicc/TypingCounter/releases)
    * 天翼网盘[下载](https://cloud.189.cn/web/share?code=FjQ36r2QzY7z（访问码：oj0u）)
2. 字数统计
首次打开软件，会在软件所在目录保存一个`typing_data.json`，用于保存每天打字的总数，软件关闭后，总次数不会清零，但是按键统计会清零。如果需要移动软件位置，现目前请一并把`typing_data.json`移动到和软件相同的目录里。
## 构建
### 环境安装
```sh
conda create -n TypingCounter python=3.11
conda activate TypingCounter
pip install -r r.txt
```

### 打包成exe
```sh
pyinstaller --onefile --windowed --icon=favicon.ico TypingCounterApp.py
```
参数说明：
* --onefile	打包成单个 .exe 文件（方便分发）
* --windowed	不要显示控制台窗口（GUI 程序必须加！否则会弹黑窗）
* --icon=icon.ico	设置程序图标（可选，文件名按你实际的改）
* TypingCounterApp.py	主程序文件 

打包完成：
1. dist/TypingCounterApp.exe ← 这就是最终可执行文件 
2. build/ ← 临时文件夹（可删除）
3. TypingCounterApp.spec ← 配置文件（可用于高级定制）


## TODO
1. 在云电脑中打字暂时统计不到，需要修改
2. 关闭后，总次数不会清零，但是按键统计会清零，是否做好当日数据保留需要根据后续使用情况而定。
3. 首次打开软件，会在软件所在目录保存一个`typing_data.json`，如果移动软件存放位置，也需要移动原来的`typing_data.json`，可能会不方便