"""
Window manager for detecting and interacting with Deezer windows
"""
import subprocess
from AppKit import NSWorkspace


class DeezerWindow:
    """Represents a Deezer window in macOS"""
    
    def __init__(self, title):
        """Initialize with window title
        
        Args:
            title (str): The window title
        """
        self.title = title


class WindowManager:
    """Manages detection and interaction with Deezer windows"""
    
    def __init__(self, logger):
        """Initialize with logger
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logger
    
    def find_deezer_windows(self):
        """Find all valid Deezer windows
        
        Returns:
            list: List of DeezerWindow instances
        """
        valid_deezer_windows = []
        
        # First, check if Deezer is running using process info
        process_info = self.get_deezer_process_info()
        if process_info and "running\": true" in process_info:
            # Try to get window title via AppleScript (most reliable)
            window_title = self._get_window_title_via_applescript()
            if window_title:
                valid_deezer_windows.append(DeezerWindow(window_title))
                return valid_deezer_windows
        
        # Fallback to NSWorkspace method
        try:
            ws = NSWorkspace.sharedWorkspace()
            running_apps = ws.runningApplications()
            
            deezer_apps = [app for app in running_apps if app.localizedName() and "deezer" in app.localizedName().lower()]
            
            if deezer_apps:
                # Try to get window title via AppleScript
                window_title = self._get_window_title_via_applescript()
                if window_title:
                    valid_deezer_windows.append(DeezerWindow(window_title))
                else:
                    # If we couldn't get the window title, use the app name
                    valid_deezer_windows.append(DeezerWindow(deezer_apps[0].localizedName()))
                
        except Exception as e:
            self.logger.error(f"Error finding Deezer windows: {e}")
        
        return valid_deezer_windows
    
    def get_active_window_title(self):
        """Get the title of the active window
        
        Returns:
            str: Window title or None if not found
        """
        print(" ┃ 🔍 Checking active window...")
        try:
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            frontmost_app_name = frontmost_app.localizedName()
            
            print(f" ┃ 🪟 Active app: {frontmost_app_name}")
            
            if "deezer" in frontmost_app_name.lower():
                print(" ┃ ✅ Deezer is active window")
                # Try to get the current song using AppleScript
                song_info = self._get_window_title_via_applescript()
                if song_info:
                    return song_info
                return frontmost_app_name
            else:
                # Even if Deezer is not active, try to get its window title
                song_info = self._get_window_title_via_applescript()
                if song_info:
                    return song_info
        except Exception as e:
            self.logger.error(f"Error getting active window title: {e}")
        
        return None
    
    def check_accessibility_permissions(self):
        """Check if Terminal has accessibility permissions on macOS
        
        Returns:
            bool: True if permissions are granted, False otherwise
        """
        print(" ┃ 🔐 Checking accessibility permissions...")
        
        # Simple AppleScript to test accessibility permissions
        test_script = '''
        tell application "System Events"
            return "Accessibility permissions are enabled"
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True
            )
            
            if result.stderr and "not allowed assistive access" in result.stderr:
                self.logger.error("Accessibility permissions not granted")
                print("\n⚠️  ACCESSIBILITY PERMISSIONS REQUIRED  ⚠️")
                print("This app needs accessibility permissions to detect song information.")
                print("Please follow these steps:")
                print("1. Open System Settings > Privacy & Security > Accessibility")
                print("2. Add Terminal (or your Python IDE) to the list")
                print("3. Make sure it's enabled (checked)")
                print("4. Restart this application\n")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error checking accessibility permissions: {e}")
            return False
    
    def _get_window_title_via_applescript(self):
        """Get window title via AppleScript
        
        Returns:
            str: Window title or None if not found
        """
        print(" ┃ 🔍 Getting Deezer window title...")
        try:
            script = '''
            tell application "System Events"
                if exists process "Deezer" then
                    tell process "Deezer"
                        if exists window 1 then
                            set windowName to name of window 1
                            return windowName
                        end if
                    end tell
                end if
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script], 
                capture_output=True, 
                text=True
            )
            
            if result.stdout.strip():
                print(f" ┃ 🪟 Window title: {result.stdout.strip()}")
                return result.stdout.strip()
                
            # If simple approach fails, try more advanced script
            script_advanced = '''
            on run
                tell application "Deezer"
                    if it is running then
                        try
                            tell application "System Events" to tell process "Deezer"
                                if exists window 1 then
                                    return name of window 1
                                end if
                            end tell
                        on error
                            # Could not get window title, try getting track info directly
                            try
                                set songName to name of current track
                                set artistName to artist of current track
                                return songName & " - " & artistName
                            end try
                        end try
                    end if
                end tell
                return ""
            end run
            '''
            
            result_advanced = subprocess.run(
                ["osascript", "-e", script_advanced], 
                capture_output=True, 
                text=True
            )
            
            if result_advanced.stdout.strip():
                print(f" ┃ 🪟 Advanced window title: {result_advanced.stdout.strip()}")
                return result_advanced.stdout.strip()
                
        except Exception as e:
            self.logger.error(f"Error executing AppleScript: {e}")
        
        print(" ┃ ⚠️ Could not get Deezer window title")
        return None
    
    def get_deezer_process_info(self):
        """Get information about the running Deezer process
        
        Returns:
            dict: Deezer process information or None if not found
        """
        print(" ┃ 🔍 Checking Deezer process info...")
        try:
            script = '''
            tell application "System Events"
                set deezerRunning to false
                set pid to 0
                set processName to ""
                
                if exists process "Deezer" then
                    set deezerRunning to true
                    set deezerProcess to process "Deezer"
                    set pid to id of deezerProcess
                    set processName to name of deezerProcess
                    
                    set windowTitles to {}
                    repeat with w in windows of deezerProcess
                        copy name of w to end of windowTitles
                    end repeat
                    
                    return "{\"running\": true, \"pid\": " & pid & ", \"name\": \"" & processName & "\", \"windows\": " & (count of windowTitles) & "}"
                end if
                
                return "{\"running\": false}"
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script], 
                capture_output=True, 
                text=True
            )
            
            if result.stdout.strip():
                print(f" ┃ 🖥️ Deezer process info: {result.stdout.strip()}")
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error getting Deezer process info: {e}")
            
        return None 