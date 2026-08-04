import os
import sys
import streamlit.web.cli as stcli

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'):
        app_path = os.path.join(sys._MEIPASS, 'src', 'web', 'app.py')
    else:
        app_path = "src/web/app.py"

    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())
