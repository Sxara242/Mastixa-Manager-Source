from app import main_window
from app.alpha2_step4_ui import install_alpha2_step4_ui
from app.alpha2_step5_ui import install_alpha2_step5_ui
from app.alpha2_ui_fixes import install_alpha2_ui_fixes
from app.crop_program_integration import install_crop_program_ui
from app.date_preferences import install_date_preferences
from app.navigation_performance import install_navigation_performance
from app.phase13_calendar_integration import install_phase13_calendar_ui
from app.plant_tracking_integration import install_plant_tracking_ui
from app.profile_login_keyboard import install_profile_login_keyboard
from app.sensor_view_integration import install_sensor_view_ui
from app.startup_lazy_pages import install_startup_lazy_pages
from app.tab_scroll_fix import install_tab_scroll_fix
from app.update_integration import install_update_ui
from app.version_integration import install_version_ui
from app.year_context_integration import install_year_context_ui
from app.desktop_navigation import install_desktop_navigation

install_alpha2_ui_fixes()
install_alpha2_step4_ui()
install_alpha2_step5_ui()
install_tab_scroll_fix()
install_update_ui()
install_version_ui()
install_navigation_performance()
install_profile_login_keyboard()
install_crop_program_ui()
install_phase13_calendar_ui()
install_plant_tracking_ui()
install_sensor_view_ui()
install_startup_lazy_pages()
install_date_preferences()
install_year_context_ui()
install_desktop_navigation()

if __name__ == "__main__":
    main_window.run_app()
