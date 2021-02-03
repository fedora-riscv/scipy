# without means enabled
%bcond_with doc

# Set to pre-release version suffix if building pre-release, else %%{nil}
%global rcver %{nil}

%if 0%{?fedora} >= 33 || 0%{?rhel} >= 9
%global blaslib flexiblas
%global blasvar %{nil}
%else
%global blaslib openblas
%global blasvar p
%endif

Summary:    Scientific Tools for Python
Name:       scipy
Version:    1.6.0
Release:    3%{?dist}

# BSD -- whole package except:
# Boost -- scipy/special/cephes/scipy_iv.c
# Public Domain -- scipy/odr/__odrpack.c
License:    BSD and Boost and Public Domain
Url:        http://www.scipy.org/scipylib/index.html
Source0:    https://github.com/scipy/scipy/releases/download/v%{version}/scipy-%{version}.tar.gz

# https://github.com/scipy/scipy/pull/13387
Patch0:     wavfile.patch

BuildRequires: fftw-devel, suitesparse-devel
BuildRequires: %{blaslib}-devel
BuildRequires: gcc-gfortran, swig, gcc-c++
BuildRequires: qhull-devel
BuildRequires: /usr/bin/pathfix.py

BuildRequires:  pybind11-devel
BuildRequires:  python3-pybind11 >= 2.4.0
BuildRequires:  python3-numpy, python3-devel, python3-numpy-f2py
BuildRequires:  python3-setuptools
BuildRequires:  python3-Cython
BuildRequires:  python3-pytest
BuildRequires:  python3-pytest-xdist
BuildRequires:  python3-pytest-timeout

%if %{with doc}
BuildRequires:  python3-sphinx
BuildRequires:  python3-matplotlib
BuildRequires:  python3-numpydoc
%endif

%global _description %{expand:
Scipy is open-source software for mathematics, science, and
engineering. The core library is NumPy which provides convenient and
fast N-dimensional array manipulation. The SciPy library is built to
work with NumPy arrays, and provides many user-friendly and efficient
numerical routines such as routines for numerical integration and
optimization. Together, they run on all popular operating systems, are
quick to install, and are free of charge. NumPy and SciPy are easy to
use, but powerful enough to be depended upon by some of the world's
leading scientists and engineers.}

%description %_description

%package -n python3-scipy
Summary:    Scientific Tools for Python
Requires:   python3-numpy, python3-f2py
%{?python_provide:%python_provide python3-scipy}
%description -n python3-scipy %_description

%if %{with doc}
%package -n python3-scipy-doc
Summary:    Scientific Tools for Python - documentation
Requires:   python3-scipy = %{version}-%{release}
%description -n python3-scipy-doc
HTML documentation for Scipy
%endif


%prep
%autosetup -p1 -n %{name}-%{version}%{?rcver}
cat > site.cfg << EOF

[amd]
library_dirs = %{_libdir}
include_dirs = /usr/include/suitesparse
amd_libs = amd

[umfpack]
library_dirs = %{_libdir}
include_dirs = /usr/include/suitesparse
umfpack_libs = umfpack

[openblas]
libraries = %{blaslib}%{blasvar}
library_dirs = %{_libdir}
EOF

# Docs won't build unless the .dat files are specified here
sed -i 's/metadata = dict(/metadata = dict(package_data={"": ["*.dat"]},/' setup.py

# remove bundled numpydoc
rm doc/sphinxext -r

rm $(grep -rl '/\* Generated by Cython') PKG-INFO

%build
for PY in %{python3_version}; do
  # Adding -fallow-argument-mismatch workaround for https://github.com/scipy/scipy/issues/11611
  env CFLAGS="$RPM_OPT_FLAGS -lm" \
  %if 0%{?fedora} >= 32 || 0%{?rhel} >= 9
      FFLAGS="$RPM_OPT_FLAGS -fPIC -fallow-argument-mismatch" \
  %else
      FFLAGS="$RPM_OPT_FLAGS -fPIC" \
  %endif
    OPENBLAS=%{_libdir} \
    FFTW=%{_libdir} BLAS=%{_libdir} LAPACK=%{_libdir} \
    %{_bindir}/python$PY setup.py config_fc \
    --fcompiler=gnu95 --noarch \
    build

  %if %{with doc}
  pushd doc
  export PYTHONPATH=$(echo ../build/lib.linux-*-$PY/)
  make html SPHINXBUILD=sphinx-build-$PY
  rm -rf build/html/.buildinfo
  mv build build-$PY
  popd
  %endif
done

%install
%py3_install
# Some files got ambiguous python shebangs, we fix them after everything else is done
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" %{buildroot}%{python3_sitearch}

%check
# check against the reference BLAS/LAPACK
export FLEXIBLAS=netlib

# default test timeout
TIMEOUT=500

%ifarch s390x
# skip failing tests on s390x for now
export PYTEST_ADDOPTS="-k '\
    not (TestNoData and test_nodata) and \
    not test_fortranfile_read_mixed_record and \
    not test_kde_1d and \
    not test_kde_1d_weighted and \
    not test_kde_2d and \
    not test_kde_2d_weighted and \
    not test_gaussian_kde_subclassing and \
    not test_gaussian_kde_covariance_caching and \
    not test_kde_integer_input and \
    not test_pdf_logpdf and \
    not test_pdf_logpdf_weighted'"

# some tests (namely test_logpdf_overflow) tend to run for a long time on s390x
TIMEOUT=1000
%endif

pushd %{buildroot}/%{python3_sitearch}
%{pytest} --timeout=${TIMEOUT} scipy --numprocesses=auto
# Remove test remnants
rm -rf gram{A,B}
popd

%files -n python3-scipy
%doc LICENSE.txt
%{python3_sitearch}/scipy/
%{python3_sitearch}/*.egg-info

%if %{with doc}
%files -n python3-scipy-doc
%license LICENSE.txt
%doc doc/build-%{python3_version}/html
%endif

%changelog
* Wed Feb 03 2021 Nikola Forró <nforro@redhat.com> - 1.6.0-3
- Increase test timeout on s390x

* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 04 2021 Nikola Forró <nforro@redhat.com> - 1.6.0-1
- New upstream release 1.6.0
  resolves: #1906692

* Wed Nov 25 2020 Nikola Forró <nforro@redhat.com> - 1.5.4-2
- Skip factorial() float tests on Python 3.10
  resolves: #1898157

* Thu Nov 05 2020 Nikola Forró <nforro@redhat.com> - 1.5.4-1
- New upstream release 1.5.4
- Increase test timeout, 300 seconds is not always enough
  for test_logpdf_overflow on s390x
  resolves: #1894887

* Mon Oct 19 2020 Nikola Forró <nforro@redhat.com> - 1.5.3-1
- New upstream release 1.5.3
  resolves: #1889132

* Wed Sep 30 2020 Nikola Forró <nforro@redhat.com> - 1.5.2-2
- Skip one more test expected to fail on 32-bit architectures

* Mon Aug 31 2020 Nikola Forró <nforro@redhat.com> - 1.5.2-1
- New upstream release 1.5.2
  resolves: #1853871 and #1840077

* Sun Aug 16 2020 Iñaki Úcar <iucar@fedoraproject.org> - 1.5.0-4
- https://fedoraproject.org/wiki/Changes/FlexiBLAS_as_BLAS/LAPACK_manager

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-3
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jun 23 2020 Elliott Sales de Andrade <quantum.analyst@gmail.com> - 1.5.0-1
- Update to latest version

* Mon May 25 2020 Miro Hrončok <mhroncok@redhat.com> - 1.4.1-2
- Rebuilt for Python 3.9

* Sun Mar 01 2020 Orion Poplawski <orion@nwra.com> - 1.4.1-1
- Update to 1.4.1 (bz#1771154)
- Workaround FTBFS with gcc 10 (bz#1800078)

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Oct 18 2019 Miro Hrončok <mhroncok@redhat.com> - 1.3.1-1
- Update to 1.3.1 (#1674101)
- Drop Python 2 packages (not supported by SciPy >= 1.3)
- Backported upstream patch for cKDTree (fixes FTBFS)

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.2.1-8
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.2.1-7
- Rebuilt for Python 3.8

* Tue Jul 30 2019 Petr Viktorin <pviktori@redhat.com> - 1.2.1-6
- Remove build dependency on python2-pytest-xdist and python2-pytest-timeout
- Enable parallel tests in Python 3 %%check
- Use macros for Python interpreter in tests

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Mon Jun 10 2019 Marcel Plch <mplch@redhat.com> - 1.2.1-4
- Fix FTBFS with Py3.8 (#1606315)

* Thu May 16 2019 Orion Poplawski <orion@nwra.com> - 1.2.1-3
- Build only against openblasp (bugz#1709161)

* Fri Apr 26 2019 Orion Poplawski <orion@nwra.com> - 1.2.1-2
- Do not create *-PYTEST.pyc files

* Tue Apr 23 2019 Orion Poplawski <orion@nwra.com> - 1.2.1-1
- Update to 1.2.1
- Drop scipy2-doc

* Wed Feb 06 2019 Charalampos Stratakis <cstratak@redhat.com> - 1.2.0-1
- Update to 1.2.0

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Sat Jun 23 2018 Miro Hrončok <mhroncok@redhat.com> - 1.1.0-2
- Don't ignore the tests results but rather have a tolerance rate
- Skip test_decomp on ppc64le as it currently segfaults

* Fri Jun 22 2018 Miro Hrončok <mhroncok@redhat.com> - 1.1.0-1
- Update to 1.1.0 (#1560265, #1594355)

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-8
- Rebuilt for Python 3.7

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 02 2018 Petr Viktorin <pviktori@redhat.com> - 1.0.0-6
- Link with -lm to build with new stricter Fedora flags
  https://bugzilla.redhat.com/show_bug.cgi?id=1541416

* Wed Jan 31 2018 Christian Dersch <lupinix@mailbox.org> - 1.0.0-5
- rebuilt for GCC 8.x (gfortran soname bump)

* Mon Dec 11 2017 Lumír Balhar <lbalhar@redhat.com> - 1.0.0-4
- Disable tests on s390x

* Mon Nov 20 2017 Lumír Balhar <lbalhar@redhat.com> - 1.0.0-3
- New subpackages with HTML documentation

* Tue Oct 31 2017 Christian Dersch <lupinix@mailbox.org> - 1.0.0-2
- Use openblas where available https://fedoraproject.org/wiki/Changes/OpenBLAS_as_default_BLAS
- Remove ppc64 hackery for OpenBLAS
- Don't run tests in parallel as pytest crashes
- Don't run test_denormals as it tends to stuck

* Thu Oct 26 2017 Thomas Spura <tomspur@fedoraproject.org> - 1.0.0-1
- update to 1.0.0 and use pytest instead of nose
- use timeout during parallel %%check

* Wed Oct 04 2017 Christian Dersch <lupinix@mailbox.org> - 0.19.1-5
- Use openblas where available (except ppc64), to use same as numpy (BZ 1472318)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.19.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.19.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 07 2017 Igor Gnatenko <ignatenko@redhat.com> - 0.19.1-2
- Rebuild due to bug in RPM (RHBZ #1468476)

* Tue Jun 27 2017 Christian Dersch <lupinix@mailbox.org> - 0.19.1-1
- new version

* Wed Jun 07 2017 Christian Dersch <lupinix@mailbox.org> - 0.19.0-1
- new version

* Tue Jan 31 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0.18.0-3
- Rebuild for libgfortran.so.3

* Mon Dec 12 2016 Stratakis Charalampos <cstratak@redhat.com> - 0.18.0-2
- Rebuild for Python 3.6

* Tue Jul 26 2016 Than Ngo <than@redhat.com> - 0.18.0-1
- 0.18.0
- %%check: make non-fatal as temporary workaround for scipy build on arm

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.17.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Tue May 31 2016 Nils Philippsen <nils@redhat.com>
- fix source URL

* Mon Feb 15 2016 Orion Poplawski <orion@cora.nwra.com> - 0.17.0-1
- Update to 0.17.0
- Drop ctypes patch applied upstream

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.16.1-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sat Nov 21 2015 Kalev Lember <klember@redhat.com> - 0.16.1-6
- Add provides to satisfy scipy%%{_isa} requires in other packages

* Sun Nov 15 2015 Björn Esser <fedora@besser82.io> - 0.16.1-5
- Revert "Discard results of testsuite on %%{arm} for now"

* Sat Nov 14 2015 Björn Esser <besser82@fedoraproject.org> - 0.16.1-4
- Discard results of testsuite on %%{arm} for now
  Segfaults on non-aligned memory test (expected for arm)

* Sat Nov 14 2015 Thomas Spura <tomspur@fedoraproject.org> - 0.16.1-3
- Add patch to fix ctypes test
- Move requires to correct python2 subpackage
- Add FFLAGS also in %%install

* Tue Nov 10 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.1-2
- Rebuilt for https://fedoraproject.org/wiki/Changes/python3.5

* Mon Oct 26 2015 Orion Poplawski <orion@cora.nwra.com> - 0.16.1-1
- Update to 0.16.1

* Wed Oct 14 2015 Thomas Spura <tomspur@fedoraproject.org> - 0.16.0-1
- Update to 0.16.0
- Use python_provide macro

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.15.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Mar 31 2015 Orion Poplawski <orion@cora.nwra.com> - 0.15.1-1
- Update to 0.15.1

* Sun Jan 4 2015 Orion Poplawski <orion@cora.nwra.com> - 0.14.1-1
- Update to 0.14.1

* Wed Aug 20 2014 Kevin Fenzi <kevin@scrye.com> - 0.14.0-5
- Rebuild for rpm bug 1131892

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat May 10 2014 Orion Poplawski <orion@cora.nwra.com> - 0.14-2
- Rebuild with Python 3.4

* Tue May  6 2014 Orion Poplawski <orion@cora.nwra.com> - 0.14-1
- Update to 0.14
- Do not use system python-six (bug #1046817)

* Thu Feb 20 2014 Thomas Spura <tomspur@fedoraproject.org> - 0.13.3-2
- use python2 macros everywhere (Requested by Han Boetes)

* Tue Feb  4 2014 Thomas Spura <tomspur@fedoraproject.org> - 0.13.3-1
- Update to 0.13.3

* Mon Dec 9 2013 Orion Poplwski <orion@cora.nwra.com> - 0.13.2-1
- Update to 0.13.2

* Fri Dec 06 2013 Nils Philippsen <nils@redhat.com> - 0.13.1-2
- rebuild (suitesparse)

* Sun Nov 17 2013 Orion Poplwski <orion@cora.nwra.com> - 0.13.1-1
- Update to 0.13.1

* Wed Oct 23 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.13.0-2
- Update to 0.13.0 final

* Tue Oct 15 2013 Orion Poplwski <orion@cora.nwra.com> - 0.13.0-0.4.rc1
- Update to 0.13.0rc1

* Tue Oct 01 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.13.0-0.3.b1
- rebuilt with atlas 3.10

* Mon Sep 9 2013 Orion Poplwski <orion@cora.nwra.com> - 0.13.0-0.2.b1
- Unbundle python-six (bug #1005350)

* Thu Aug 29 2013 Orion Poplwski <orion@cora.nwra.com> - 0.13.0-0.1.b1
- Update to 0.13.0b1
- Drop patches applied upstream
- Fixup changelog and summary

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.12.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 30 2013 Tomas Tomecek <ttomecek@redhat.com> - 0.12.0-4
- Fix rpmlint warnings
- License update
- Add patch to use build_dir argument in build_extension

* Wed May 15 2013 Orion Poplawski <orion@cora.nwra.com> - 0.12.0-3
- Remove old ufsparse references, use suitesparse
- Spec cleanup

* Mon Apr 15 2013 Orion Poplawski <orion@cora.nwra.com> - 0.12.0-2
- Add patch to fix segfaul in test of sgeqrf

* Wed Apr 10 2013 Orion Poplawski <orion@cora.nwra.com> - 0.12.0-1
- Update to 0.12.0 final
- No longer remove weave from python3 build

* Sat Feb 16 2013 Orion Poplawski <orion@cora.nwra.com> - 0.12.0-0.1.b1
- Update to 0.12.0b1
- Drop upstreamed linalg patch

* Wed Feb 13 2013 Orion Poplawski <orion@cora.nwra.com> - 0.11.0-4
- Add patch from upstream to fix python3.3 issues in linalg routines

* Tue Feb 12 2013 Orion Poplawski <orion@cora.nwra.com> - 0.11.0-3
- Disable python3 tests for now

* Mon Oct  8 2012 Orion Poplawski <orion@cora.nwra.com> - 0.11.0-2
- Add requires python3-numpy, python3-f2py for python3-scipy (bug 863755)

* Sun Sep 30 2012 Orion Poplawski <orion@cora.nwra.com> - 0.11.0-1
- Update to 0.11.0 final

* Thu Aug 23 2012 Orion Poplawski <orion@cora.nwra.com> - 0.11.0-0.1.rc2
- Update to 0.11.0rc2

* Mon Aug  6 2012 Orion Poplawski <orion@cora.nwra.com> - 0.10.1-4
- Rebuild for python 3.3

* Fri Aug  3 2012 David Malcolm <dmalcolm@redhat.com> - 0.10.1-3
- remove rhel logic from with_python3 conditional

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.10.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Mar 16 2012 Orion Poplawski <orion@cora.nwra.com> - 0.10.1-1
- Update to 0.10.1

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.10.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Nov 14 2011 Orion Poplawski <orion@cora.nwra.com> - 0.10.0-1
- Update to 0.10.0

* Sat Sep  3 2011 Thomas Spura <tomspur@fedoraproject.org> - 0.9.0-2
- little cosmetic changes
- filter provides in python_sitearch

* Fri Sep 02 2011 Andrew McNabb <amcnabb@mcnabbs.org>
- add python3 subpackage

* Fri Apr 1 2011 Orion Poplawski <orion@cora.nwra.com> - 0.9.0-1
- Update to 0.9.0
- Drop all stsci sources and patches, dropped from upstream
- Drop gcc and py27 patches fixed upstream
- Add %%check section to run tests

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Jul 31 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.7.2-3
- Fix scipy build on python-2.7

* Thu Jul 22 2010 David Malcolm <dmalcolm@redhat.com> - 0.7.2-2
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Thu Jul 1 2010 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.2-1
- New upstream release

* Sun Apr 11 2010 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.1-3
- Bump for rebuild against numpy 1.3

* Thu Apr  1 2010 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.1-2
- Bump for rebuild against numpy 1.4.0

* Thu Dec 10 2009 Jon Ciesla <limb@jcomserv.net> - 0.7.1-1
- Update to 0.7.1.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun Jun 14  2009 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.0-4
- Fix for gcc34 weave blitz bug #505379

* Tue Apr 7  2009 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.0-3
- Add f2py requires to prepared for numpy packaging split

* Sun Mar 1  2009 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.0-2
- Patch for stsci image function syntax fix.

* Thu Feb 26 2009 Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.0-1
- Update to final 0.7 release

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.0-0.3.b1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Dec 15 2008 Deji Akingunola <dakingun@gmail.com> - 0.7.0-0.2.b1
- Rebuild for atlas-3.8.2

* Mon Dec 01 2008  Jef Spaleta <jspaleta@fedoraproject.org> - 0.7.0-0.1.b1
- Update to latest beta which lists python 2.6 support

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.6.0-8
- Rebuild for Python 2.6

* Fri Oct 03 2008 Jef Spaleta <jspaleta@fedoraproject.org> - 0.6.0-7
- fix the stsci fix

* Thu Oct 02 2008 Jef Spaleta <jspaleta@fedoraproject.org> - 0.6.0-6
- include missing setup files for stsci module

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 0.6.0-5
- Autorebuild for GCC 4.3

* Fri Jan 04 2008 Jef Spaleta <jspaleta@fedoraproject.org> - 0.6.0-4
- fix for egg-info file creation

* Wed Oct 03 2007 Jef Spaleta <jspaleta@gmail.com> - 0.6.0-3
- include_dirs changes for ufsparse change in development

* Tue Oct 02 2007 Jef Spaleta <jspaleta@gmail.com> - 0.6.0-2
- Fix licensing to match Fedora packaging guidance
- Remove unnecessary library deps

* Tue Sep 25 2007 Jarrod Millman <millman@berkeley.edu> - 0.6.0-1
- update to new upstream source
- update Summary, License, Url, and description
- added extra dependencies
- remove symlink since Lib has been renamed scipy

* Tue Aug 21 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2.1-1
- Update to new upstream source

* Tue Aug 21 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-3
- fix licensing tag and bump for buildid rebuild

* Wed Apr 18 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-2.2
- go back to using gfortran now that numpy is patched

* Sat Apr 14 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-2.1
- minor correction for f77 usage

* Sat Apr 14 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-2
- revert to f77 due to issue with numpy in development

* Sat Apr 14 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-1.1
- remove arch specific optimizations

* Wed Feb 21 2007 Jef Spaleta <jspaleta@gmail.com> - 0.5.2-1
- Update for new upstream release

* Mon Dec  11 2006 Jef Spaleta <jspaleta@gmail.com> - 0.5.1-5
- Bump for rebuild against python 2.5 in devel tree

* Sun Dec  3 2006 Jef Spaleta <jspaleta@gmail.com> - 0.5.1-4
- Minor adjustments to specfile for packaging guidelines.
- Changed buildrequires fftw version 3  from fftw2

* Sat Dec  2 2006 Jef Spaleta <jspaleta@gmail.com> - 0.5.1-2
- Updated spec for FE Packaging Guidelines and for upstream version 0.5.1

* Mon May  8 2006 Neal Becker <ndbecker2@gmail.com> - 0.4.8-4
- Add BuildRequires gcc-c++
- Add python-devel
- Add libstdc++

* Mon May  8 2006 Neal Becker <ndbecker2@gmail.com> - 0.4.8-3
- Add BuildRequires gcc-gfortran

* Sun May  7 2006 Neal Becker <ndbecker2@gmail.com> - 0.4.8-3
- Add BuildRequires numpy


* Wed May  3 2006 Neal Becker <ndbecker2@gmail.com> - 0.4.8-2
- Fix BuildRoot
- Add BuildRequires, Requires
- Test remove d1mach patch
- Fix defattr
- Add changelog
- Removed Prefix, Vendor
- Fix Source0
