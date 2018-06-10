import argparse
from typing import Optional
from typing import Sequence

from all_repos import cli
from all_repos.config import load_config

BASH = '''\
__all_repos__clone_opts="$(git clone --help | grep -Eo -- '--[a-zA-Z0-9-]+')"

# https://github.com/scop/bash-completion/blob/d2f14a7/bash_completion#L498
__all_repos__ltrim_colon_completions() {
    if [[ "$1" == *:* && "$COMP_WORDBREAKS" == *:* ]]; then
        # Remove colon-word prefix from COMPREPLY items
        local colon_word=${1%"${1##*:}"}
        local i=${#COMPREPLY[*]}
        while [[ $((--i)) -ge 0 ]]; do
            COMPREPLY[$i]=${COMPREPLY[$i]#"$colon_word"}
        done
    fi
}

_git_clone() {
    case "$cur" in
    --*)
        __gitcomp "$__all_repos__clone_opts"
        return
        ;;
    *)
        argc=0
        for word in "${words[@]}"; do
            case "$word" in
            git|clone|--*)
                continue
                ;;
            *)
                argc=$((argc + 1))
                ;;
            esac
        done

        if [ $argc -le 1 ]; then
            __gitcomp "$(jq --raw-output .[] "$__all_repos__repos_json")"
            __all_repos__ltrim_colon_completions "$cur"
        fi
        ;;
    esac
}
'''

ZSH = '''\
__git_remote_repositories() {
    local -a options
    options=( $(
        jq -r \
           'to_entries | map([.value, .key]|join("\\t")) | join("\\n")' \
           "$__all_repos__repos_json" |
            sed 's/:/\\\\:/; s/\\t/:/'
    ) )
    _describe 'values' options
}
'''


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Add git-clone tab completion for all-repos repositories.\n\n'
            'Add to .bash_profile:\n'
            '  `eval "$(all-repos-complete -C ~/.../all-repos.json --bash)"`'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage='%(prog)s [options] {--bash}',
    )
    cli.add_common_args(parser)
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument('--bash', action='store_true')
    mutex.add_argument('--zsh', action='store_true')
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)

    print(f'__all_repos__repos_json={config.repos_filtered_path}')
    if args.bash:
        print(BASH)
    elif args.zsh:
        print(ZSH)
    else:
        raise NotImplementedError()
    return 0


if __name__ == '__main__':
    exit(main())
