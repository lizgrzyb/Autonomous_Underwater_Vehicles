import arcade

# 设置屏幕尺寸
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# 打开窗口
arcade.open_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Custom Origin Example")
arcade.set_background_color(arcade.color.WHITE)

# 开始渲染
arcade.start_render()

arcade.set_viewport(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0)

# 绘制一个矩形，测试新的坐标系
arcade.draw_rectangle_filled(50, 50, 30, 30, arcade.color.BLUE)  # 在左上角附近绘制一个矩形

# 绘制文本，确保正常显示
arcade.draw_text(
    "Hello, Arcade!",
    100, 50,
    arcade.color.BLACK,
    24
)

# 结束渲染
arcade.finish_render()

# 保持窗口打开
arcade.run()