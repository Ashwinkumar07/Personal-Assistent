from tools.registry import ToolRegistry
from tools.builtins.system_tools import (
    GetCurrentTimeTool,
    GetCurrentDateTool,
    GetSystemSpecsTool,
    GetBatteryStatusTool,
    GetActiveWindowTitleTool,
    GetClipboardTool,
    SetClipboardTool,
    LaunchAppTool,
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
from tools.builtins.camera_tool import InspectCameraSnapshotTool

def register_default_tools(registry: ToolRegistry) -> None:
    """Register the standard safe built-in tools."""
    tools = [
        GetCurrentTimeTool(),
        GetCurrentDateTool(),
        GetSystemSpecsTool(),
        GetBatteryStatusTool(),
        GetActiveWindowTitleTool(),
        GetClipboardTool(),
        SetClipboardTool(),
        LaunchAppTool(),
        ListDirectoryTool(),
        ReadTextFileTool(),
        SearchFilesTool(),
        WriteTextFileTool(),
        CreateDirectoryTool(),
        CopyFileTool(),
        MoveFileTool(),
        DeleteFileTool(safety_gate=registry.safety_gate),
        InspectCameraSnapshotTool(),
    ]
    for tool in tools:
        registry.register(tool)
