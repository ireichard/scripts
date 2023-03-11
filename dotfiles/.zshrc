_MIN_MODE_OFF=0
_MIN_MODE_ON=1

# Custom aliases
alias cls='clear'
alias toilet='toilet -t'
alias _trn='tr -d "\n"'
alias echn='echo -n'
alias pcs='pokemon-colorscripts'
alias mm='cat ~/.minimal-mode'
alias _mmdis='echo -n "$_MIN_MODE_OFF" > ~/.minimal-mode && MIN_MODE_ON="$_MIN_MODE_OFF"'
alias _mmen='echo -n "$_MIN_MODE_ON" > ~/.minimal-mode && MIN_MODE_ON="$_MIN_MODE_OFF"'
alias mmdis='_mmdis && clear && source ~/.zshrc'
alias mmen='_mmen && clear && source ~/.zshrc'

# Set minimum mode
if [ -e ~/.minimal-mode ]; then
	MIN_MODE_ON=$(cat ~/.minimal-mode | _trn)
else
	echo '.minimum-mode missing, creating and disabling it.'
	_mmdis
fi

# Rice
# User and system info
echn '\033[1;31m' && id -un | _trn && echn '\033[0m@'\
&& echn '\033[0;32m' && uname -n | _trn && echn ' \033[0mon '\
&& uname -p | _trn && echn ' ' && uname -o | _trn && echn ' ' && uname -r | _trn\
&& echn ' ' && uname -v | cut -d ' ' -f1
# Uptime info
uptime -p | _trn && echn ' | ' && uptime -s
# Fancy ricing
if [ "$MIN_MODE_ON" -eq '0' ]; then
	pcs --no-title --name "$(uname -n)"
else
	echo 'minimal mode is ON.'
fi
