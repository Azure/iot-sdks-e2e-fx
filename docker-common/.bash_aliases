alias ls=ls

if [ ! -f /root/.vimrc ]; then
    printf "\
        set tabstop=4\n\
        set softtabstop=4\n\
        set expandtab\n\
        set showmatch\n\
        set shiftwidth=4\n\
        filetype plugin indent on\n\
        syntax off\n\
        " > /root/.vimrc
fi
export LD_LIBRARY_PATH=/restbed/distribution/library
