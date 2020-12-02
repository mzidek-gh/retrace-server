Summary: Application for remote coredump analysis
Name: retrace-server
Version: 1.22.4
Release: 1%{?dist}
License: GPLv2+
URL: https://github.com/abrt/retrace-server
Source0: https://github.com/abrt/%{name}/archive/%{version}/%{name}-%{version}.tar.gz

%if 0%{?fedora} >= 29
# There are Python plugins in /usr/share/retrace-server/plugins
%global _python_bytecompile_extra 0
%endif

BuildArch: noarch

BuildRequires: asciidoc
BuildRequires: gettext
BuildRequires: gzip
BuildRequires: lsof
BuildRequires: lsof
BuildRequires: meson
BuildRequires: python3-devel
BuildRequires: tar
BuildRequires: texinfo
BuildRequires: xmlto
BuildRequires: xz

Requires: rsync
Requires: mock >= 1.4.7
Requires: xz
Requires: gzip
Requires: bzip2
Requires: tar
Requires: p7zip
Requires: unzip
Requires: lzop
Requires: lsof
Requires: elfutils
Requires: createrepo_c
Requires: python3-createrepo_c
Requires: python3-mod_wsgi
Requires: python3-webob
Requires: python3-magic
Requires: python3-requests
Requires: python3-requests-gssapi
Requires: python3-bugzilla
Requires: python3-dnf
Requires: python3-hawkey
Requires: mod_ssl
Requires: sqlite
Requires: crash >= 5.1.7
Requires: wget
Requires: kexec-tools
Requires: distribution-gpg-keys
%if (0%{?rhel} && 0%{?rhel} <= 7) || (0%{?fedora} && 0%{?fedora} <= 27)
Requires(preun): /sbin/install-info
Requires(post): /sbin/install-info
%endif
Requires(post): /usr/bin/crontab
Recommends: podman
Recommends: logrotate

Obsoletes: abrt-retrace-server < 2.0.3
Provides: abrt-retrace-server = 2.0.3

%description
The retrace server provides a coredump analysis and backtrace
generation service over a network using HTTP protocol.

%prep
%autosetup

%build
%meson \
    -Ddocs=enabled \
    %{nil}
%meson_build

%install
%meson_install

# Remove byte-compiled python files generated by automake.
# automake uses system's python for all *.py files, even
# for those which needs to be byte-compiled with different
# version (python2/python3).
# rpm can do this work and use the appropriate python version.
find %{buildroot} -name "*.py[co]" -delete

mkdir -p %{buildroot}%{_localstatedir}/cache/%{name}
mkdir -p %{buildroot}%{_localstatedir}/cache/%{name}/kernel
mkdir -p %{buildroot}%{_localstatedir}/cache/%{name}/download
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_sharedstatedir}/retrace
mkdir -p %{buildroot}%{_libexecdir}/%{name}
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_start
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/start
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_prepare_debuginfo
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/post_prepare_debuginfo
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_prepare_environment
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/post_prepare_environment
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_retrace
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/post_retrace
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/success
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/fail
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_remove_task
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/post_remove_task
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/pre_clean_task
mkdir -p %{buildroot}%{_libexecdir}/%{name}/hooks/post_clean_task

%if 0%{?fedora} >= 29
%py_byte_compile %{__python3} %{buildroot}%{_datadir}/%{name}/plugins
%endif

rm -f %{buildroot}%{_infodir}/dir

%{find_lang} %{name}

%pre
#retrace uid/gid reserved in setup, rhbz #706012
%define retrace_gid_uid 174
getent group retrace > /dev/null || groupadd -f -g %{retrace_gid_uid} --system retrace
getent passwd retrace > /dev/null || useradd --system -g retrace -u %{retrace_gid_uid} -d %{_sharedstatedir}/retrace -s /sbin/nologin retrace
exit 0

%post
%if (0%{?rhel} && 0%{?rhel} <= 7) || (0%{?fedora} && 0%{?fedora} <= 27)
/sbin/install-info %{_infodir}/%{name} %{_infodir}/dir 2> /dev/null || :
%endif
/usr/sbin/usermod -a -G mock retrace 2> /dev/null || :

if [ "$1" = 1 ]
then
#add disabled crontab entries to retrace's crontab
    %define retrace_crontab_entry0 "# 0 * * * * /usr/bin/retrace-server-cleanup >> /var/log/retrace-server/cleanup_error.log 2>&1"
    %define retrace_crontab_entry1 "#0 0,12 * * * /usr/bin/retrace-server-reposync fedora 15 i386 >> /var/log/retrace-server/reposync_error.log 2>&1"
    %define retrace_crontab_entry2 "#0 2,14 * * * /usr/bin/retrace-server-reposync fedora 15 x86_64 >> /var/log/retrace-server/reposync_error.log 2>&1"
    %define retrace_crontab_entry3 "#0 4,16 * * * /usr/bin/retrace-server-reposync fedora 16 i386 >> /var/log/retrace-server/reposync_error.log 2>&1"
    %define retrace_crontab_entry4 "#0 6,18 * * * /usr/bin/retrace-server-reposync fedora 16 x86_64 >> /var/log/retrace-server/reposync_error.log 2>&1"
    %define retrace_crontab_entry5 "#0 8,20 * * * /usr/bin/retrace-server-reposync fedora rawhide i386 >> /var/log/retrace-server/reposync_error.log 2>&1"
    %define retrace_crontab_entry6 "#0 10,22 * * * /usr/bin/retrace-server-reposync fedora rawhide x86_64 >> /var/log/retrace-server/reposync_error.log 2>&1"

    (crontab -u retrace -l 2> /dev/null; echo %{retrace_crontab_entry0}; \
     echo %{retrace_crontab_entry1}; echo %{retrace_crontab_entry2}; \
     echo %{retrace_crontab_entry3}; echo %{retrace_crontab_entry4}; \
     echo %{retrace_crontab_entry5}; echo %{retrace_crontab_entry6};) | crontab -u retrace - 2> /dev/null
fi
exit 0

%preun
if [ "$1" = 0 ]
then
%if (0%{?rhel} && 0%{?rhel} <= 7) || (0%{?fedora} && 0%{?fedora} <= 27)
    /sbin/install-info --delete %{_infodir}/retrace-server %{_infodir}/dir 2> /dev/null || :
%endif
#comment entries in retrace's crontab
    (crontab -u retrace -l 2> /dev/null | sed "s,^\([^#].*\)$,#\1,g") | crontab -u retrace - 2> /dev/null
fi
exit 0

%files -f %{name}.lang
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}-httpd.conf
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%config(noreplace) %{_sysconfdir}/%{name}/%{name}-hooks.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/debuginfo.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/fail.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/environment.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/retrace.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/start.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/success.conf
%config(noreplace) %{_sysconfdir}/%{name}/hooks/task.conf
%dir %{_sysconfdir}/logrotate.d
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%dir %attr(0755,retrace,retrace) %{_localstatedir}/cache/%{name}
%dir %attr(0755,retrace,retrace) %{_localstatedir}/cache/%{name}/kernel
%dir %attr(0755,retrace,retrace) %{_localstatedir}/cache/%{name}/download
%dir %attr(0750,retrace,retrace) %{_localstatedir}/log/%{name}
%dir %attr(0770,retrace,retrace) %{_localstatedir}/spool/%{name}
%dir %{_sysconfdir}/%{name}
%dir %attr(0775,root,retrace) %{_libexecdir}/%{name}
%{_bindir}/%{name}-worker
%{_bindir}/%{name}-interact
%{_bindir}/%{name}-cleanup
%{_bindir}/%{name}-reposync
%{_bindir}/%{name}-reposync-faf
%{_bindir}/%{name}-plugin-checker
%{_bindir}/%{name}-task
%{_bindir}/%{name}-bugzilla-refresh
%{_bindir}/%{name}-bugzilla-query
%{_bindir}/coredump2packages
%{python3_sitelib}/retrace/
%{_datadir}/%{name}/
%dir %attr(0755,retrace,retrace) %{_sharedstatedir}/retrace/
%attr(0775,root,retrace) %{_libexecdir}/%{name}/hooks/
%doc %{_mandir}/man1/%{name}-cleanup.1*
%doc %{_mandir}/man1/%{name}-interact.1*
%doc %{_mandir}/man1/%{name}-reposync.1*
%doc %{_mandir}/man1/%{name}-worker.1*
%doc %{_mandir}/man1/%{name}-task.1*
%doc %{_infodir}/%{name}*
%doc README.md
%license COPYING

%changelog
* Tue Nov 24 2020 Matěj Grabovský <mgrabovs@redhat.com> 1.22.4-1
- Make retrace-server-reposync-faf work again
- Update list of Fedora versions shown on stats page: remove releases before 31
  and Fedora 33
- Do not allocate pseudo-TTY for Podman container
- Remove intermediate Podman containers even after image build fails
- Reformat manager page to improve readability (dwysocha@redhat.com)
- Rework display of finished, running, and available tasks (dwysocha@redhat.com)
- Update translations

* Fri Oct 30 2020 Matěj Grabovský <mgrabovs@redhat.com> 1.22.3-1
- Fix coredump2packages script to run properly

* Fri Oct 23 2020 Matěj Grabovský <mgrabovs@redhat.com> 1.22.2-1
- Fix path to coredump in generated dockerfile when using Podman backend
- Fix "not writable" error when retracing coredumps
- Improve log messages

* Wed Oct 21 2020 Matěj Grabovský <mgrabovs@redhat.com> 1.22.0-1
- Add support for virtual memory files for vmcores
- Add option to restart an existing task in retrace-server-task and on task manager page
- Disallow users other than 'retrace' to call retrace-server-worker
- Improve error message in case of Kerberos authentication failure
- Revamp task manager web UI
- Revamp GPG verification of package signatures; use keys from distribution-gpg-keys
- Accommodate for multiple debug directories in Fedora 27 and later
- Fix FTP submissions on task manager page
- Fix permissions on dmesg file in task results directory
- Migrate build process to Meson; completely drop Autotools
- Add Tito configuration
- Update translations
- Drop python3-six dependency
- Add build dependencies on gzip, lsof, tar and xz
- Rewrite Dockerfile
- Migrate to calling subprocess.run() in place of s.Popen() and s.call()
- Use pathlib.Path instead of strings and os.path methods in some places
- Add kernel-only config options 'KernelDebuggerPath' and 'RetraceEnvironment=native'
- Introduce type annotations
- Address issues reported by Pylint
- Other minor code refactoring and cleanup operations

* Wed Oct 21 2020 Matěj Grabovský <mgrabovs@redhat.com> 1.22.0-1
- Add support for virtual memory files for vmcores
- Add option to restart an existing task in retrace-server-task and on task manager page
- Disallow users other than 'retrace' to call retrace-server-worker
- Improve error message in case of Kerberos authentication failure
- Revamp task manager web UI
- Revamp GPG verification of package signatures; use keys from distribution-gpg-keys
- Accommodate for multiple debug directories in Fedora 27 and later
- Fix FTP submissions on task manager page
- Fix permissions on dmesg file in task results directory
- Update translations
- Drop python3-six dependency
- Add build dependencies on gzip, lsof, tar and xz
- Rewrite Dockerfile
- Migrate to calling subprocess.run() in place of s.Popen() and s.call()
- Use pathlib.Path instead of strings and os.path methods in some places
- Add kernel-only config options 'KernelDebuggerPath' and 'RetraceEnvironment=native'
- Introduce type annotations
- Address issues reported by Pylint
- Other minor code refactoring and cleanup operations

* Fri Feb 07 2020 Michal Fabik <mfabik@redhat.com> 1.21.0-1
- README: Add translation status
- translations: Remove zanata config and script
- retrace: Fix bytes has no attribute encode
- Fix error when calling run_crash_cmdline after conversion to run()
- Fix error handling when unknown exception occurs in run_crash_cmdline
- podman: Tweak the Dockerfile for retracing
- Remove rpm2cpio part from podman retrace
- Check for RequireGPGCheck
- Simplify run calls
- Make returncode checks more readable
- Fix container and image cleanup
- Tag podman images with task id
- Replace call() and Popen() with run()
- Fix container cleanup
- Change home dir for user 'retrace'
- Use more meaningful log messages
- Replace os.devnull with subprocess.DEVNULL
- Add podman-specific deployment instructions
- Fix pylint issues
- Run hooks with podman as well
- Add UseFafPackages support in podman
- Fix indentation
- Add exit code to spec file scriptlet
- Add podman as a weak dependency
- Beautify gdb.sh
- Run retrace in podman container
- Create Dockerfiles
- Make mock-specific parts conditional
- Remove test for abrt-gdb-exploitable
- Add RetraceEnvironment config item
- Fix spelling
- Tweak man pages
- Update translations
- r-s-reposync-faf: Fix paths to rpms
- Update (pt) translation
- Update (nl) translation
- Update (de) translation
- Update (bg) translation
- Update (tr) translation
- Update (it) translation
- Add (zh_HK) translation
- r-s-reposync: Replace old way of cmp with key
- README.md: Change capitalization of freenode
- Fix build error after change of mock.conf to environment.conf
- hooks: Rename mock hook to environment
- hooks: Add option for per-executable timeouts
- spec: Remove upgrade script moving config to new location
- hooks:config: Load configs from users homedir
- hooks: Move default hook script dir to /usr/libexec
- hooks: Log stdout and stderr of scripts after exception
- hooks: Run hook scripts in parallel processes
- spec: Do not replace configs on reinstall
- hooks: Fix hook timeouts and other exceptions logs
- hooks: Change cwd for hooks to hooks dir
- hooks: Change of retrace hooks
- config: Move retrace-server configuration file
- retrace: Change logging format
- retrace_worker: Remove distro hack from mock config
- dockerfile_local: Install vim
- docker: Update Makefile
- docker: Use sbin/httpd instead of apachectl
- dockerfile_local: Install make
- dockerfile: Update to Fedora 31
- dockerfile: Install mod_ssl
- retrace_worker: Fix file mode to write to file
- retrace-server-worker: Correct import of ArgumentParser

* Tue Oct 29 2019 Michal Fabik <mfabik@redhat.com> 1.20.0-1
- Bump Fedora Release in Dockerfile
- retrace_worker: Use kernelver_str var
- retrace_worker: Remove unused variables
- retrace: Remove unused variable
- retrace: Use converted integer value
- retrace: Remove unsused variable
- pylint: Fix wrong indentations
- pylint W0702: Fix-up bare exceptions
- pylint: Fix spacing issues
- Remove Python2/Python3 compatibility code
- pylint E713: Test for membership should be ‘not in’
- retrace: Refactor asterisk imports of retrace
- Translation updates
- Add new translation languages - tr
- Add transtalations from Fedora Zanata
- Remove workdir functionality
- retrace-server-interact: Fix undefined self var
- retrace: Fix undefined vmcore variable
- Fix typos
- Fix typos and minor grammar issues
- Switch to requests-gssapi
- create: Fix strip_extra_pages() invocation
- plugins: Add el8 to versionlist
- plugins: Add plugin for CentOS
- plugins: Update fedora versionlist
- plugins: Update devtoolset version
- stats: Display whole release version
- Use sys.exit instead of exit for retrace-server commands
- Move makedumpfile logic from download_remote into start_vmcore
- Move prepare_debuginfo to KernelVMcore
- Remove call to prepare_debuginfo from retrace-server-interact
- Move get_kernel_release to KernelVMcore
- Move strip_vmcore to KernelVMcore.strip_extra_pages
- Add KernelVMcore.has_extra_pages method
- Move get_vmcore_dump_level to KernelVMcore.get_dump_level
- Handle 'flattened' vmcore format by converting with makedumpfile
- Pass 'results' directory to hook script rather than task_dir.
- Rename 'misc' methods and subdirectory to 'results'.
- delete: Fix typo in function name
- Clean up handling of mock with x86 vmcores in x86_64 environments
- Remove bt_filter from retrace-server
- Remove excess post-retrace crash commands
- Make retrace-server-cleanup more resilient to non-existent tasks
- retrace: Allow tilde in package names
- spec: Use macros instead of environment variables
- Fix module extraction from kernel-debuginfo
- Move ProcessCommunicateTimeout inside run_crash_cmdline
- Move run_crash_cmdline from RetraceWorker to RetraceTask
- Fix backtrace of bt_filter on Python3
- Remove 'utf-8' encoding for run_crash_cmd and change related functions.
- Refactor crash commands run after prepare_debuginfo into run_crash_cmdline helper
- worker: Add string formatting for provided arguments
- worker: Remove unused function
- worker: Use log_error function to log errors
- Fix runaway crash processes due to either corrupted vmcore memory or files.
- Fix backtrace when updating bugzillano from web UI due to use of basestring
- Fix message and code path when we fail to decode the release of vmcore
- spec: Fix test condition for Fedora
- spec: Fix %if conditions
- spec: Add python3-createrepo_c dependency
- retrace_worker: Ignore EEXISTS when symlinking log
- retrace: Replace execfile with exec(open())
- Drop YUM support
- Drop __future__.print_function import
- Drop __future__.division import
- Fix ftp.wsgi for Python3 due to sorted() method change, speed manager load
- Fix get_kernel_release() on Python3
- cleanup: Add check for opened crash files
- Add forgotten encoding
- reposync: Inform why creating of repository failed

* Mon Aug 27 2018 Martin Kutlak <mkutlak@redhat.com> 1.19.0-1
- docker: Allow building local changes
- docker: Introduce docker
- spec: Require Python3 pkgs of dnf and hawkey
- retrace: Check result of get_nevra_possibilities
- r-s-reposync-faf: Convert generator to list
- spec: Add BuildRequire python3-devel
- r-s-reposync-faf: Generate repo using createrepo_c
- httpd-conf: Set WSGIApplicationGroup to %{GLOBAL}
- r-s-reposync: Use default number of workers
- dnf-comp: Replace yum.misc lib with one from dnf
- py3-comp: Distinguish string and byte values in POST
- py3-comp: Specify encoding for Popen
- py3-comp: Use parentheses for print
- py3-comp: Encode response body as a bytestring
- py3-comp: Convert regexps strings to raw strings
- Migrate retrace-server to python3
- Implement splitFilename function using dnf
- Replace yum with DNF
- Correct syntax for gdb backtrace command
- Refactoring: Too long lines, missing whitespaces
- Add has_coredump() method to RetraceTask and upate get_md5_tasks()
- Modify get_md5_tasks to skip tasks with no vmcores or invalid md5sum files
- Add 'has_vmcore' method to RetraceTask
- spec: Bytecompile r-s plugins explicitly
- spec: Remove automake byte-compiled files
- spec: Correct the file ownership
- do not require install-info on F28+
- Adjust indentation according to pylint recommendation
- py3 compatibility: Replace filter function with a list equivalent
- py3 compatibility: Adjust urllib, urllib2 and urlparse
- Fix missing sys import
- Clean up of unused imports
- py3 compatibility: Adjust imports
- py3 compatibility: Resolution of range and xrange
- py3 compatibility: Replace ConfigParser module with configparser
- py3 compatibility: Classic division
- py3 compatibility: Adjust raise statement syntax
- py3 compatibility: Replace StringIO module with io module
- py3 compatibility: Removal of tuple parameter unpacking
- Refactoring: Missing or bad whitespace
- py3 compatibility: Set literals
- py3 compatibility: Use 'sorted' built-in function
- py3 compatibility: Replacement of basestring with six.string_types
- py3 compatibility: Ensure map function to return a list
- py3 compatibility: Replacement of 'has_key' with 'in'
- Make r-s-bugzilla-query query options configurable
- Load credentials from custom file
- manager: Make the bugzillano a clickable link
- Query the remaining bugzilla statuses
- retrace: Add reset_age method
- Implement retrace-server-bzquery tool
- Implement retrace-server-bugzilla-refresh tool
- Implement bugzilla field
- py3 compatibility: Octal literals
- py3 compatibility: try-except statement
- py3 compatibility: print statement is replaced with a print() function
- For vmcores that fail crash but have a large enough kernel log, try --minimal
- Set md5sum as soon as possible.
- Add dedup_vmcore to RetraceWorker and call from retrace-server-cleanup
- Fail task if the crash sys command exits with non-zero and kernellog is small
- Fix typo in exception handling of get_kernel_release
- Set default signal handler for SIGPIPE before calling Popen on 'crash --osrelease'
- Improve vmcore kernel parsing for certain scenarios and limit file scanning
- autogen: correctly parse buildrequires from spec file
- spec: Do not:x show every single change

* Thu Feb 01 2018 Matej Marusak <mmarusak@redhat.com> 1.18.0-1
- mark license as license
- Update Python 2 dependency declarations to new packaging standards
- defattr is not needed as this is default
- use standard python_sitelib macro
- remove old changelog entries
- we do not build for el6 any more
- remove group
- Remove duplicate RetraceWorker._fail call when start_vmcore fails
- Add md5sum and kernelver to email notifications, help text to failing notification
- Convert notify_email_success and notify_email_fail to a single method
- Create notify_email_success / notify_email_fail helpers
- Enable packages with epoch
- Update to new mock
- Set kernelver and vmlinux as soon as possible
- reposync: Cleanup is not done by default in createrepo
- Explicitly state python version in shebangs
- Fix unreadable crash subdirectory when tarball is submitted without group read permissions
- Try noarch when checking for package
- Add pylintrc
- Use dnf in mock config on Fedora
- Update mock config for new mock version
- Pylint updates
- Add commandline client
- Add aliases into FAF reposync
- Cleanup tmp FAF repository after failing
- Write coresize for vmcores
- Change error message
- Fix wrong html tag
- Set zero to non-existing type of tasks
- Fix typeo in manager.wsgi which creates a backtrace on non-ftp tasks.
- Bump version of gettext
- Change path for README.md
- Fix problem with missing modules on kernel versions with cached vmlinux files.
- No first retrace time when no existing task
- Make the reposync tool more verbose if required

* Thu Mar 30 2017 Matej Marusak <mmarusak@redhat.com> 1.17.0-1
- Enable creating releases with makefile
- Introduce gen-version
- Do not use fedorahosted.org as source
- Include md5sum of original archive in summary page
- Do not try to get default time when ftptask
- Fix character escape typo
- Change retrace-server httpd config
- Modify search for existing vmlinux files in cache to handle older kernel-debuginfos
- Default to hex mode for crash commands involving backtraces.
- Create directories for tests if they are not present
- Don't mention old wiki page
- Fix double call of _fail method
- Update README
- Allow any compression of man pages
- Autogen without args configures for debugging
- Run 'configure' at the end of 'autogen'
- Improve autogen to list and install dependencies
- Avoid circular dependency on kernel-debuginfo for vmlinux files already in cache
- Add plugin checking action
- Update documentation of plugin in README
- Use short form rhel when creating repository
- Fix methods arguments
- Move global variables to config.py.in
- Recover from missing start/finish task files
- Change error message in cleanup script
- Add '-ascending' argument to gdb
- Use devtoolset-4-gdb when used on RHEL
- Enable creating repository from faf repository
- Add 'make check'
- Correct eu-unstrip parser if FILE is .
- Not mark packages with different architectures as duplicity
- Separate worker start_retrace method
- Add class to wrap plugins accessing
- Add class to wrap configuration file reading
- Delete python labels when no python backtrace available
- Git ignore bytecode
- Add python backtrace, source and locals into backtrace
- Move src/lib to src/retrace to make testing retrace-server easier
- Add "exploitable" into LocationMatch in the httpd.conf
- Fix invalid syntax error in sys.stderr.print()

* Thu Jun 2 2016 Jakub Filak <jfilak@redhat.com> - 1.16-1
- Log failed to start tasks
- Gracefully handle the worker errors
- Move the FTP query operation to an AJAX operation
- Fix duplicate email if a vmcore task fails to determine the kernel version
- Fix typo preventing email notifications from working.
- Correct eu-unstrip parser if FILE is '-'
- Allow package names with Epoch

* Fri Mar 18 2016 Jakub Filak <jfilak@redhat.com> - 1.15-1
- Correct paths to Fedora development releases
- Fix small problem with strip_vmcore calling prepare_debuginfo
- Avoid calling prepare_debuginfo from retrace-server-interact after kernel version detection
- Move prepare_debuginfo and strip_vmcore inside RetraceTask
- Add vmlinux file inside RetraceTask
- Fix bt_filter missing last task/PID read if the last line was not blank
- Update the release information to be dynamic based off of plugins
- Including a Red Hat Enterprise Linux plugin
- Mock logging into retrace task's dir
- Enforce uniform mode bits for almost all RetraceTask files
- Fix incorrect group permissions when writing RetraceServer files especially with interactive mode
- Fix retrace-server-worker --restart backtrace due to unwriteable retrace_log
- Correct license address
- Add VMCoreTask and UsrCoreTask to config

* Tue Feb 16 2016 Jakub Filak <jfilak@redhat.com> - 1.14-1
- generated config.py for the target platform at build time
- update URL patterns for Fedora repositories
- spec: add sqlite and cron to requirements
- set "crash" inside get_crash_cmd file if the file does not exist
- fix get_use_mock typo
- use %%global for the nested python_site macro instead of %%define
