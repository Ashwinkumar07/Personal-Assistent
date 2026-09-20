from tools.registry import ToolRegistry
from tools.builtins.system_tools import (
    GetCurrentTimeTool,
    GetCurrentDateTool,
    GetSystemSpecsTool,
    GetBatteryStatusTool,
    GetActiveWindowTitleTool,
    GetClipboardTool,
    SetClipboardTool,
)
from tools.builtins.file_tools import (
    ListDirectoryTool,
    ReadTextFileTool,
    SearchFilesTool,
    WriteTextFileTool,
    CreateDirectoryTool,
    CopyFileTool,
    MoveFileTool,
    DeleteFileTool,
)

def register_default_tools(registry: ToolRegistry) -> None:
    """Register the 15 standard safe built-in tools."""
    tools = [
        GetCurrentTimeTool(),
        GetCurrentDateTool(),
        GetSystemSpecsTool(),
        GetBatteryStatusTool(),
        GetActiveWindowTitleTool(),
        GetClipboardTool(),
        SetClipboardTool(),
        ListDirectoryTool(),
        ReadTextFileTool(),
        SearchFilesTool(),
        WriteTextFileTool(),
        CreateDirectoryTool(),
        CopyFileTool(),
        MoveFileTool(),
        DeleteFileTool(safety_gate=registry.safety_gate),
    ]
    for tool in tools:
        registry.register(tool)
