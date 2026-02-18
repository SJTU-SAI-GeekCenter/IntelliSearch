from ui.permission_ui import handle_permission_error
from mcp_server.operate_file.security import ImplicitDenyError

# 模拟一个未授权错误
# 假设 Agent 想访问 d:/geek-centre/IntelliSearch/config/test_config.yaml
fake_error = ImplicitDenyError(
    "Access Denied: No known permission rule covers d:\\geek-centre\\IntelliSearch\\config\\test_config.yaml."
)
fake_path = "d:/geek-centre/IntelliSearch/config/test_config.yaml"

print("\n--- Preview UI Start ---\n")

# 虽然这里是 Mock 执行，但它会真实地调用 rich print 和 input
# 请在 Terminal 交互测试
try:
    result = handle_permission_error(fake_error, context_path=fake_path)
    print(f"\nResult: {'Authorized' if result else 'Denied'}")
except Exception as e:
    # 可能会因为 security_manager 真实写入失败而报错，但 UI 应该能显示
    print(f"\n(UI Preview finished with backend action: {e})")
