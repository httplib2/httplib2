CACHE_DIR=$HOME/.cache
SSL_INSTALL=$CACHE_DIR/ssl
PYTHON_INSTALL=$CACHE_DIR/python

rm -rf $CACHE_DIR/* # temp blow away

if [ ! -f $CACHE_DIR/python/bin/python ]; then
  ORIGINAL_DIRECTORY=$(pwd)
  PYTHON_VERSION="3.7.3"
  OPENSSL_VERSION="1.1.1c"
  echo "RUNNING: apt update..."
  sudo apt-get -qq --yes update > /dev/null
  echo "RUNNING: apt dist-upgrade..."
  sudo apt-get -qq --yes dist-upgrade > /dev/null
  echo "Installing build tools..."
  sudo apt-get -qq --yes install build-essential > /dev/null
  echo "Installing deps for python3..."
  sudo cp -v /etc/apt/sources.list /tmp
  sudo chmod a+rwx /tmp/sources.list
  dist=$(lsb_release --codename --short)
  echo "deb-src http://archive.ubuntu.com/ubuntu/ $dist main" >> /tmp/sources.list
  sudo cp -v /tmp/sources.list /etc/apt
  sudo apt-get -qq --yes update > /dev/null
  sudo apt-get -qq --yes build-dep python3 > /dev/null

  cpucount=$(nproc --all)
  cd $CACHE_DIR

  # Compile OpenSSL
  if [ ! -d openssl-$OPENSSL_VERSION ]; then
    wget --quiet https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
    echo "Extracting OpenSSL..."
    tar xf openssl-$OPENSSL_VERSION.tar.gz
  fi
  cd openssl-$OPENSSL_VERSION
  echo "Compiling OpenSSL $OPENSSL_VERSION..."
  ./config shared --prefix=$SSL_INSTALL
  echo "Running make for OpenSSL..."
  make -j$cpucount -s
  echo "Running make install for OpenSSL..."
  make install > /dev/null
  export LD_LIBRARY_PATH=$SSL_DIR/lib
  cd ..

  # Compile latest Python
  if [ ! -d Python-$PYTHON_VERSION ]; then
    wget --quiet https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz
    echo "Extracting Python..."
    tar xf Python-$PYTHON_VERSION.tar.xz
  fi
  cd Python-$PYTHON_VERSION
  echo "Compiling Python $PYTHON_VERSION..."
  # Note we are purposefully NOT using optimization flags as they increase compile time 10x
  conf_flags="--with-openssl=$SSL_DIR --enable-shared --prefix=$PYTHON_INSTALL --with-ensurepip=upgrade"
  ./configure $conf_flags > /dev/null
  make -j$cpucount -s
  echo "Installing Python..."
  make install > /dev/null
  ln -s $PYTHON_INSTALL/bin/python3 $PYTHON_INSTALL/bin/python
  ln -s $PYTHON_INSTALL/bin/pip3 $PYTHON_INSTALL/bin/pip
  cd $ORIGINAL_DIRECTORY
fi

export LD_LIBRARY_PATH=$PYTHON_INSTALL/lib:$SSL_INSTALL/lib
export PATH=$PYTHON_INSTALL/bin:$SSL_INSTALL/bin:$PATH
