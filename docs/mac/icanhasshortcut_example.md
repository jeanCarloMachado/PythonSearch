[main]
config version = 2
shell = /Users/jean.machado/projects/personalscripts/myZsh
populate_menu_with_actions = yes
show_hotkeys_in_menu = yes
check_for_updates = yes
start_on_login = yes
show_icon_in_statusbar = yes
set_workdir_with_cd = no
window_x = 811
window_y = 272
window_width = 600
window_height = 300
shortcut_column_enabled = yes
action_column_enabled = yes
command_column_enabled = yes
workdir_column_enabled = no
shortcut_column_width = 80
action_column_width = 100
command_column_width = 120
workdir_column_width = 100

[shortcut1]
shortcut = ⌘Space
action = search run
command = log_command.sh search_run search
workdir =
enabled = yes

[shortcut2]
shortcut = ⌘↩
action =
command = open -a iTerm .
workdir =
enabled = yes

[shortcut3]
shortcut = ⌘M
action = gmail
command = search_run run_key 'gmail client application force open'
workdir =
enabled = yes

[shortcut4]
shortcut = ⌘0
action = copy now
command = search_run run_key 'date current today now min and seconds copy'
workdir =
enabled = yes

[shortcut5]
shortcut = ⌘1
action = whatsapp
command = search_run run_key 'whatsapp webapp'
workdir =
enabled = yes

[shortcut6]
shortcut = ⌥R
action = add new
command = search_run register_new infer_from_clipboard
workdir =
enabled = yes

[shortcut7]
shortcut = ⇧⌥R
action = register snippet
command = search_run register_new snippet_from_clipboard
workdir =
enabled = yes

[shortcut8]
shortcut = ⌘J
action = journaling
command = search_run run_key 'journaling workflowy'
workdir =
enabled = yes

[shortcut9]
shortcut = ⌃⌘T
action = translator
command = search_run run_key 'google translator app'
workdir =
enabled = yes

[shortcut10]
shortcut = ⌥V
action = life visionlife vision board
command = search_run run_key 'life vision board'
workdir =
enabled = yes

[shortcut11]
shortcut = ⇧⌘C
action = calendar
command = search_run run_key 'google calendar'
workdir =
enabled = yes

[shortcut12]
shortcut = ⌘T
action = email task
command = search_run run_key 'type email task'
workdir =
enabled = yes

[shortcut13]
shortcut = ⇧⌃R
action = drafts and notes
command = search_run run_key 'drafts and notes'
workdir =
enabled = yes

[shortcut14]
shortcut = ⌘B
action = browser
command = search_run run_key 'chrome browser mac'
workdir =
enabled = yes

[shortcut15]
shortcut = ⌥S
action = spotify
command = open -a Spotify
workdir =
enabled = yes

[shortcut16]
shortcut = ⌥2
action = jira board
command = search_run run_key 'python search jira board'
workdir =
enabled = yes
