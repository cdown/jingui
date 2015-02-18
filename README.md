[![Linux build status][travis-image]][travis-builds]
[![Coverage][coveralls-image]][coveralls]
[![Code health][landscape-image]][landscape]
[![Dependencies][requires-image]][requires]

[travis-builds]: https://travis-ci.org/cdown/jingui
[travis-image]: https://img.shields.io/travis/cdown/jingui/master.svg?label=build
[coveralls]: https://coveralls.io/r/cdown/jingui
[coveralls-image]: https://img.shields.io/coveralls/cdown/jingui/master.svg
[landscape]: https://landscape.io/github/cdown/jingui/master
[landscape-image]: https://landscape.io/github/cdown/jingui/master/landscape.svg
[requires]: https://requires.io/github/cdown/jingui/requirements/?branch=master
[requires-image]: https://img.shields.io/requires/github/cdown/jingui.svg?label=deps

[jingui][] (from "金柜/金匱" ("strongbox"), or perhaps "[金龟/金龜][]" if it is
running particularly slowly on your machine ;-)), is a simple password manager
designed to adhere to the Unix philosophy. It uses [NaCL][] for encryption and
signing, and [git][] for history.

## Work in progress

Be warned, jingui is very much a work in progress. Much of the stuff you will
read below has either not been implemented yet, or has only been partially
implemented. You should not expect any kind of security from this version of
jingui.

## Usage

First, make sure you have git set up as required. If you don't, take a look at
the [Git documentation][] to learn more.

Now that we've got the Git set up, we can start to add passwords and other
metadata. Make sure [`$EDITOR`][] or [`$VISUAL`][] are set appropriately in
your environment.

    # Add a new password in your editor, or edit an existing one
    jg -e example

    # Add a username
    jg -e example username

    # You can also use slashes instead of separate arguments
    jg -e example/username

These hierarchies are totally arbitrary, you can use whatever hierarchies make
sense to you.

Once you've edited the file, it will be encrypted with PGP by GPG and stored in
Git. You can now copy it to your clipboard, or show it in your terminal:

    # Copy password for "example" to clipboard
    jg example

    # Show username for "example"
    jg -s example username

As you've probably noticed, the first positional argument specifies the
service, and the second specifies the type of data to retrieve (the "field").
As mentioned above, these hierarchies are only a suggestion, you can use any
hierarchy structure that makes sense to you. Both of these arguments can
contain arbitrary data, which means that if you have two accounts on a service,
you can do something like this:

    # Copy password for personal Google account
    jg google personal

    # Copy password for work Google account
    jg google work

## Implementation details

Each piece of metadata in the hierarchy is stored in a separate file. The main
motivation for this is to avoid conflicts in Git when merging other changes.
The filenames of these files are pseudorandom UUIDs, they are not linked to the
content.

When editing the files, the temporary files are stored in memory if at all
possible. I suggest you also make sure that your editor doesn't leave its data
lying around on disk.

## Motivation for creation

For a few years now, I have used (and helped develop, although less in recent
times) [pass][], which uses [GPG][] and [git][] to manage passwords. However,
it has some limitations that I don't like:

- No concept of metadata, everything other than the password is stored as
  freeform text and is not easily usable. This makes it difficult to easily use
  metadata at a later point, instead relying on manual intervention;
- The original script has become quite convoluted, largely due to corner cases
  and complexity compromises that are for edge-case systems;
- Commands like `generate` overwrite metadata, metadata is treated as a
  second-class citizen;
- Filenames are not encrypted, they are stored raw.

jingui is quite similar to pass (which very much inspired it), but it is
designed to be much more flexible without losing the simplicity (both in user
experience and use of existing tools) that makes pass great. Here are some ways
that jingui attemps to alleviate the problems mentioned above:

- jingui treats everything (usernames, passwords, etc) as metadata. There are
  no special provisions for passwords. This ensures that metadata other than
  passwords is not treated as a second-class citizen;
- jingui attempts to have test coverage for all situations that can occur when
  using the program;
- jingui errs towards simplicity rather than functionality, and the internal
  code is clean and clearly separates functionality into different objects;
- jingui uses [NaCL][] instead of GPG because the bindings are much more stable
  and the API is better defined (`python-gnupg` is a good library, but no good
  for bleeding edge systems as releases lag behind GPG mainline and are often
  totally broken on such systems for this reason);
- jingui does not have any connection between the filename a piece of metadata
  gets and the name of the metadata. Instead, random UUIDs are generated for
  each separate metadata file.

Each entry in jingui is a plain text file, encrypted and signed using your PGP
key. The default action is to copy a password to your clipboard, but you can
show it by using `-s`.

[jingui]: https://github.com/cdown/jingui
[pass]: http://www.passwordstore.org/
[GPG]: https://www.gnupg.org/
[git]: http://git-scm.com/
[GPG's getting started document]: https://www.gnupg.org/gph/en/manual/c14.html
[Git documentation]: http://git-scm.com/doc
[`$EDITOR`]: http://en.wikibooks.org/wiki/Guide_to_Unix/Environment_Variables#EDITOR
[`$VISUAL`]: http://en.wikibooks.org/wiki/Guide_to_Unix/Environment_Variables#VISUAL
[金龟/金龜]: http://baike.baidu.com/view/395421.htm
[NaCL]: http://nacl.cr.yp.to
