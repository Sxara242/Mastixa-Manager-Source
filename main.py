from app import main_window
from app.crop_program_integration import install_crop_program_ui
from app.navigation_performance import install_navigation_performance
from app.phase13_calendar_integration import install_phase13_calendar_ui
from app.plant_tracking_integration import install_plant_tracking_ui
from app.profile_login_keyboard import install_profile_login_keyboard
from app.sensor_view_integration import install_sensor_view_ui
from app.startup_lazy_pages import install_startup_lazy_pages

install_navigation_performance()
install_profile_login_keyboard()
install_crop_program_ui()
install_phase13_calendar_ui()
install_plant_tracking_ui()
install_sensor_view_ui()
install_startup_lazy_pages()

if __name__ == "__main__":
    main_window.run_app()
