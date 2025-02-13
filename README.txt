# kevitivity@gmail.com
#
# pcm.py is Python script that provides a command-line interface for managing
PAM configurations.

Basic operations/examples 

# List all PAM services
./pam_manager.py --action list

# Show rules for a specific service
./pam_manager.py --action show --service system-auth

# Add a new rule
./pam_manager.py --action add --service system-auth --type auth --control required --module pam_unix.so --args "nullok try_first_pass"

# Remove rules containing a specific module
./pam_manager.py --action remove --service system-auth --module pam_unix.so

Safety features:

Creates backups before making changes
Validates input parameters
Requires root privileges for production use
Can work in a test directory if not running as root
