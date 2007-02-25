%define python_sitearch %(%{__python} -c 'from distutils import sysconfig; print sysconfig.get_python_lib(1)')

Summary: Scipy: array processing for numbers, strings, records, and objects
Name: scipy
Version: 0.5.2
Release: 1%{?dist}

Group: Development/Libraries
License: BSD
Url: http://numeric.scipy.org
Source0: http://prdownloads.sourceforge.net/scipy/%{name}-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: numpy, python-devel 
BuildRequires: fftw-devel, blas-devel, lapack-devel, gcc-gfortran

Requires: numpy, python


%description
Scipy is a general-purpose array-processing package designed to
efficiently manipulate large multi-dimensional arrays of arbitrary
records without sacrificing too much speed for small multi-dimensional
arrays.  Scipy is built on the Numeric code base and adds features
introduced by numarray as well as an extended C-API and the ability to
create arrays of arbitrary type.

There are also basic facilities for discrete fourier transform,
basic linear algebra and random number generation.


%prep
%setup -q

%build
env CFLAGS="$RPM_OPT_FLAGS" ATLAS=%{_libdir} FFTW=%{_libdir} BLAS=%{_libdir} LAPACK=%{_libdir} python setup.py config_fc --fcompiler=gnu95 build

%install
rm -rf $RPM_BUILD_ROOT
env CFLAGS="$RPM_OPT_FLAGS" ATLAS=%{_libdir} FFTW=%{_libdir} BLAS=%{_libdir} LAPACK=%{_libdir} python setup.py config_fc --fcompiler=gnu95 install --root=$RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files 
%defattr(-,root,root,-)
%doc LICENSE.txt
%{python_sitearch}/scipy



%changelog
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

