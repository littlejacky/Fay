
=======
[`English`](https://github.com/xszyou/Fay/blob/main/README_EN.md)

<div align="center">
    <br>
    <img src="images/icon.png" alt="Fay">
    <h1>FAY</h1>
	<h3>Fay数字人框架 带货版</h3>
</div>



Fay数字人框架 带货版用于构建：虚拟主播、现场推销货、商品导购，等数字人应用场景。该项目各模块之间耦合度非常低，包括声音来源、语音识别、情绪分析、NLP处理、情绪语音合成、语音输出和表情动作输出等模块。每个模块都可以轻松地更换。



如果你需要的是一个人机交互的数字人助理，请移步 [`助理完整版`](https://github.com/xszyou/Fay/tree/fay-assistant-edition)

如果你需要是一个可以自主决策、主动联系主人的agent，请移步[`agent版`](https://github.com/xszyou/Fay/tree/fay-agent-edition)               

如果你需要的是一个人机交互的数字人助理，请移步 [`助理完整版`](https://github.com/TheRamU/Fay/tree/fay-assistant-edition)

如果你需要是一个可以自主决策、主动联系主人的agent，请移步[`agent版`](https://github.com/TheRamU/Fay/)               

![](images/cs.png)



![](images/controller.png)




## **安装说明**

### **环境** 
- Python 3.10

### **安装依赖**

```shell
pip install -r requirements.txt
```

### **配置应用**
+ 配置 `./system.conf` 文件

### **启动**
启动Fay控制器
```shell
python main.py
```



## **使用说明**


### **使用说明**

+ 抖音虚拟主播：启动bin/Release_2.85/2.85.exe  +  fay控制器（抖音输入源开启）+ 数字人 + 抖音伴侣（测试时直接通过浏览器打开别人的直播间）；

+ 现场推销货：fay控制器（填写商品信息）+ 数字人；

+ 商品导购：fay控制器（麦克风输入源开启、填写商品信息、填写商品Q&A）+ 数字人；

  

  b站字幕监测源码：https://github.com/wangzai23333/blivedm
  
  抖音监测源码：https://github.com/wwengg/douyin

  视频号监测源码：https://github.com/fire4nt/wxlivespy

  操作教程：[bilibili个性化数字人直播教程（不封号，有流量奖励）_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV14h4y1N716/)


商务QQ 467665317

关注公众号（fay数字人）获取最新微信技术交流群二维码（请先star本仓库）

![](images/gzh.jpg)





