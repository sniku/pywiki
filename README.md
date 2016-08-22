pywiki
======

This is very simple terminal interface (TUI) for managing personal mediawiki installation.

I have a mediawiki installation on personal server for storing various notes, ranging from family addresses to code 
snippets, configuration files and commands I rarely use and can't remember.

While standard web-interface is functional, you have to launch a browser and it takes numerous clicks to find anything. 
I find it much more convenient to use `$ wiki my_commands` or `$ wiki search IP` as shown below:

# Installation
pywiki supports both python2 and python3. If you have a choice, use python3.

Recommended way is to use PyPI:
```shell
sudo pip3 install pywiki  # or sudo pip install pywiki
```

or, if you want to install from source:

```shell
git clone git@github.com:sniku/pywiki.git
cd pywiki
sudo python3 setup.py install  # or sudo python2 setup.py install
```

# Configuration

create a config file in `~/.config/wiki_client.conf`

```shell
cat ~/.config/wiki_client.conf

[defaults]
# This is the only required config directive, all the others are optional.
MEDIAWIKI_URL: http://mywiki.example.net/

# force an editor. Otherwise your default editor will be used.
# I use vim, but you can use gedit or "gvim --nofork" or whatever you like.
FORCE_EDITOR: vim
    
# This is only required if you want to edit articles as a logged in user. (You have to create an account first)
MEDIAWIKI_USERNAME: wikiuser
MEDIAWIKI_PASSWORD: wikipassword
    
# This is only required if your wiki installation is behind an additional HTTP auth.
HTTP_AUTH_USERNAME: httpauth_user
HTTP_AUTH_PASSWORD: httpauth_password
```
#### VIM syntax coloring
If you happen to use `vim` as your editor, you may want to copy the vim 
syntax coloring files for nicer editing experience.
`cp -r pywiki/vim ~/.vim`

### Most common use case

Most common use case is to open specific article for editing or viewing
`$ wiki my_article`

Ar this point article `my_article` will be opened in your text editor.
If article doesn't exist, it will be created.

### Usage:
```
wiki
wiki [go] <article_name>
wiki [go] <article_name> < stdin_file.txt
wiki append <article_name> <text>
wiki log <article_name> <text>
wiki cat <article_name>
wiki mv <article_name> <new_name>
wiki upload <filepath> [<alt_filename>]
wiki --help
```
### Interactive mode
    
This goes to interactive mode:

```
$ wiki
 Wiki command: go my_commands 
 Opening "my_commands"  # at this point your default editor is opened with the content of "my_commands"
 Saving "my_commands"
```
#### Searching for a note
```
$ wiki
Wiki command: /IP  # this is shortcut for "search IP"
Searching for "IP"
1: Sysadmin tools 
	 nmap -sT -PN -n -sV -p- 192.168.5.63 # scan the shit out of this IP == ip configuration ==
2: Kzk notes 
	 select ip , count( ip ) as ile group by ip 
3: Network 
	 IP : 192.168.5.254
4: Work notes 
	 Subnet mask Example IP 
    
Select 1, 2, 3, 4 to open the article

Wiki command: 3
Opening "Network" # opens content of "Network" in your default editor
```

#### Uploading a file

By default mediawiki requires you to log-in before you can upload a file so fill in your username and password in the 
config file first. 
    
`$ wiki upload ~/path/to/file.txt`

#### Quick edits

This is the a quick way to append short text to the end of your article:

`$ wiki append my_article "some text here"`
    
It's great for integrating with other programs. You can run this for example in cron.

There's alternative version if you want to append text from a text file:

`$ wiki my_article < ~/path/to/some_file.txt`
    
There's also a logging function:

`$ wiki log my_article "I did a thing!"`
    
This results in appending something like this to the end of the article:

    2016-08-21 15:54 I did a thing!

