
# from terminal.command_executor import CommandExecutor
import subprocess
from langchain.tools import tool


@tool
def execute_command(command: str) -> str:
    """Execute a command in the terminal."""

    # executor = CommandExecutor()

    # return executor.execute(command)

    res = ''
    try:
        # 如果你想获得终端命令的输出，用 capture_output=True
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        res = f'命令输出:\n{result.stdout}'
        return res
    except subprocess.CalledProcessError as e:
        res = f'命令执行失败:\n{e}\n错误信息:\n{e.stderr}'
        return res

if __name__ == "__main__":
    execute_command.invoke(
        {
            "command": "dir"
        }
    )
    print(execute_command("dir"))