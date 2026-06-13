# 命令

/usage
/model
/context
/clear



# 选择文件

`@`

# 快捷键

两次ctrl+c,快速退出，一次清除输入的提示词



## 对话恢复

- 粗力度： 
    - /resume 恢复历史对话
    - claude --continue
- 细粒度： 两次esc 进入到rewind  （时光回退）能够恢复之前修改的代码


# Bash命令

`! pnpm run dev` `ctrl+b`可以将它挂起，在底部可以看到运行的bash.通过电脑方向键↓可以看到shell的运行情况。这里运行的结果，**claude code是可以看到的**,出现问题的时候，在dev下可以很方便将控制台信息交给claude code.

不让claude code看到是`ctrl+z` suspend claude code, 输入`fg`恢复对话

## 权限命令

`settings.local.json`里面记录了在与claude code运行执行的命令。这可以是在对话过程中claude code动态生成的，也可以是自己手动编辑。

```json
{
  "permissions": {
    "allow": [
      "Bash(npx react-router *)",
      "Bash(npx tsc *)",
      "Bash(pnpm *)",
      "WebSearch"
    ],
    "deny": [
      "Bash(git push *)"
    ]
  }
}
```

# Context Windows

建议在40%的时候就要开始警惕了

![](./images/context_window.png)


# 用到的提示词

fetch info about react-route typegen from the web