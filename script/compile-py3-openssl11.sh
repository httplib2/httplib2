if [ ! -f $HOME/.cache/python/bin/python ]; then
  ORIGINAL_DIRECTORY=$(pwd)
  PYTHON_VERSION="3.7.3"
  OPENSSL_VERSION="1.1.1c"
  echo "RUNNING: apt update..."
  sudo apt-get -qq --yes update > /dev/null
  echo "RUNNING: apt dist-upgrade..."
  sudo apt-get -qq --yes dist-upgrade > /dev/null
  echo "Installing build tools..."
  sudo apt-get -qq --yes install build-essential > /dev/null
  echo "Installing deps for python3"
  sudo cp -v /etc/apt/sources.list /tmp
  sudo chmod a+rwx /tmp/sources.list
  echo "deb-src http://archive.ubuntu.com/ubuntu/ $dist main" >> /tmp/sources.list
  sudo cp -v /tmp/sources.list /etc/apt
  sudo apt-get -qq --yes update > /dev/null
  sudo apt-get -qq --yes build-dep python3 > /dev/null

  cpucount=$(nproc --all)
  cd $HOME/.cache

  # Compile OpenSSL
  if [ ! -d openssl-$OPENSSL_VERSION ]; then
    wget --quiet https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
    echo "Extracting OpenSSL..."
    tar xf openssl-$OPENSSL_VERSION.tar.gz
  fi
  cd openssl-$OPENSSL_VERSION
  echo "Compiling OpenSSL $OPENSSL_VERSION..."
  ./config shared --prefix=$HOME/.cache/ssl
  echo "Running make for OpenSSL..."
  make -j$cpucount -s
  echo "Running make install for OpenSSL..."
  make install > /dev/null
  export LD_LIBRARY_PATH=$HOME/.cache/ssl/lib
  cd ..

  # Compile latest Python
  if [ ! -d Python-$PYTHON_VERSION ]; then
    wget --quiet https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz
    echo "Extracting Python..."
    tar xf Python-$PYTHON_VERSION.tar.xz
  fi
  cd Python-$PYTHON_VERSION
  echo "Compiling Python $PYTHON_VERSION..."
  conf_flags="--with-openssl=$HOME/.cache/ssl --enable-shared --prefix=$HOME/.cache/python --with-ensurepip=upgrade"
  ./configure $conf_flags > /dev/null
  make -j$cpucount -s
  echo "Installing Python..."
  make install > /dev/null
  ln -s $HOME/.cache/python/bin/python3 $HOME/.cache/python/bin/python
  ln -s $HOME/.cache/python/bin/pip3 $HOME/.cache/python/bin/pip
  cd $ORIGINAL_DIRECTORY
fi

export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
export PATH=$HOME/.cache/python/bin:$PATH
