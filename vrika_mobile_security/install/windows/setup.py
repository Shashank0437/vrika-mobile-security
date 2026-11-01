"""Static Analysis Setup Windows.

Setup script for the Windows vm for usage with Vrika for
static analysis of Windows apps.
"""
import configparser
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
from os.path import expanduser

try:
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlrequest


logger = logging.getLogger(__name__)

# pylint: disable=C0325,W0603

# Only static URL, let's hope this never changes..
CONFIG_URL = (
    'https://raw.githubusercontent.com/Vrika/'
    'vrika-mobile-security/master/'
    'vrika_mobile_security/install/windows/config.txt'
)

# Static path to config file as a starting point
CONFIG_PATH = expanduser('~') + '\\Vrika\\Config\\'
CONFIG_FILE = 'config.txt'

# Static path to autostart
AUTOSTART = (
    expanduser('~') + '\\AppData\\Roaming\\Microsoft\\'
    'Windows\\Start Menu\\Programs\\Startup\\'
)

# Global var so we don't have to pass it every time..
CONFIG = ''


def windows_config_local(path):
    """Windows Configuration."""
    # Configure here if you are on windows
    # Path to lock-file (so setup is only run once)
    path_to_lock_file = os.path.join(path, 'setup_done.txt')
    if (os.path.isfile(path_to_lock_file) is False
            and platform.system() == 'Windows'
            and 'CI' not in os.environ):
        logger.info('Running first time setup for windows.')
        # Setup is to-be-executed
        install_locally(path)


def download_config():
    """Download initial config file."""
    # Create config path
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(CONFIG_PATH)

    if os.path.exists(CONFIG_PATH + CONFIG_FILE):
        os.remove(CONFIG_PATH + CONFIG_FILE)

    # TODO(Give user time to modify config, but mayber after rewrite?)

    # Open File
    conf_file_local = open(CONFIG_PATH + CONFIG_FILE, 'wb')

    # Downloading File
    print('[*] Downloading config file..')
    conf_file = urlrequest.urlopen(CONFIG_URL)  # pylint: disable-msg=E1101

    # Save content
    print(('[*] Saving to File {}'.format(CONFIG_FILE)))

    # Write content to file
    conf_file_local.write(bytes(conf_file.read()))

    # Aaaand close
    conf_file_local.close()


def read_config():
    """Read the config file and write it to the global var."""
    print('[*] Reading config file..')

    global CONFIG
    CONFIG = configparser.ConfigParser()
    CONFIG.read(CONFIG_PATH + CONFIG_FILE)


def create_folders():
    """Create Vrika dirs."""
    print('[*] Creating other folders...')

    if not os.path.exists(CONFIG['Vrika']['downloads']):
        os.makedirs(CONFIG['Vrika']['downloads'])

    if not os.path.exists(CONFIG['Vrika']['tools']):
        os.makedirs(CONFIG['Vrika']['tools'])

    if not os.path.exists(CONFIG['Vrika']['samples']):
        os.makedirs(CONFIG['Vrika']['samples'])

    if not os.path.exists(CONFIG['Vrika']['key_path']):
        os.makedirs(CONFIG['Vrika']['key_path'])


def check_dependencies():
    """Check dependencies and install if necessary."""
    print('[*] Checking dependencies...')
    missing_deps = []

    try:
        import cryptography  # noqa F401
        print('[+] cryptography is installed.')
    except ImportError:  # pylint: disable-msg=C0103
        print('[!] cryptography not installed!')
        missing_deps.append('cryptography')

    if len(missing_deps) > 0:
        print('[!] Please install these missing dependencies:')
        print(missing_deps)
        sys.exit()
    else:
        print('[+] Everything good.')


def tools_nuget():
    """Download nuget."""
    # Get config params
    nuget_url = CONFIG['nuget']['url']
    vrika_subdir_tools = CONFIG['Vrika']['tools']
    nuget_file_path = CONFIG['nuget']['file']

    # Open File
    nuget_file_local = open(os.path.join(
        vrika_subdir_tools, nuget_file_path), 'wb')

    # Downloading File
    print('[*] Downloading nuget..')
    nuget_file = urlrequest.urlopen(nuget_url)  # pylint: disable-msg=E1101

    # Save content
    print(('[*] Saving to File {}'.format(nuget_file_path)))

    # Write content to file
    nuget_file_local.write(bytes(nuget_file.read()))

    # Aaaand close
    nuget_file_local.close()


def tools_binskim():
    """Download and extract binskim."""
    # Get dirs, urls etc.
    binskim_nuget = CONFIG['binskim']['nuget']
    vrika_subdir_tools = CONFIG['Vrika']['tools']
    nuget = vrika_subdir_tools + CONFIG['nuget']['file']

    print('[*] Downloading and installing Binskim...')
    # Execute nuget to get binkim
    output = subprocess.check_output(
        [
            nuget,
            'install', binskim_nuget, '-Pre',
            '-Version', '1.7.2',
            '-o', vrika_subdir_tools])

    # Some code to determine the version on the fly so we don't have to fix the
    # config file on every new release of binskim..

    # Search for the version number
    folder = re.search(
        b'Microsoft\\.CodeAnalysis\\.BinSkim\\..{0,300}(\'|\") ', output)
    try:
        # Substring-Foo for removing b'X's in python3
        if sys.version_info.major == 3:
            folder = str(folder.group(0)[:-2])[2:-1]
        else:
            folder = folder.group(0)[:-2]
    except AttributeError:
        print('[!] Unable to parse folder from binskim nuget installation.')
        sys.exit()

    # Search for the exes
    binaries = _find_exe(vrika_subdir_tools + folder, [])
    if len(binaries) != 2:
        print('[!] Found more than 2 exes for binskim, panic!')
        sys.exit()

    # Determinde which one is for which arch
    if 'x86' in binaries[0]:
        CONFIG['binskim']['file_x86'] = binaries[0]
        CONFIG['binskim']['file_x64'] = binaries[1]
    else:
        CONFIG['binskim']['file_x86'] = binaries[1]
        CONFIG['binskim']['file_x64'] = binaries[0]

    # Write to config
    with open(os.path.join(CONFIG_PATH, CONFIG_FILE), 'w') as configfile:
        CONFIG.write(configfile)  # pylint: disable-msg=E1101


def _find_exe(path, exe_list):
    """Return a list of all exes in path, recursive."""
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            if '.exe' in filename:
                exe_list.append(path + '\\' + filename)
        else:
            exe_list = _find_exe(path + '\\' + filename, exe_list)
    return exe_list


def tools_rpcclient():
    """Download and install rpc-server for Vrika."""
    rpc_url = CONFIG['rpc']['url']
    vrika_subdir_tools = CONFIG['Vrika']['tools']
    rpc_file_path = CONFIG['rpc']['file']

    # Open File
    rpc_local_file = open(vrika_subdir_tools + rpc_file_path, 'wb')

    # Downloading File
    print('[*] Downloading rpc_server..')
    rpc_file = urlrequest.urlopen(rpc_url)

    # Save content
    print(('[*] Saving to File {}'.format(rpc_file_path)))

    # Write content to file
    rpc_local_file.write(bytes(rpc_file.read()))

    # Aaaand close
    rpc_local_file.close()


def tools_binscope():
    """Download and install Binscope for Vrika."""
    vrika_subdir_tools = CONFIG['Vrika']['tools']
    binscope_path = vrika_subdir_tools + 'BinScope'

    # Download the right version for os
    if platform.machine().endswith('64'):
        binscope_url = CONFIG['binscope']['url_x64']
        binscope_installer_path = binscope_path + '\\BinScope_x64.msi'
    else:
        binscope_url = CONFIG['binscope']['url_x86']
        binscope_installer_path = binscope_path + '\\BinScope_x86.msi'

    if not os.path.exists(binscope_path):
        os.makedirs(binscope_path)

    binscope_installer_file = open(binscope_installer_path, 'wb')

    # Downloading File
    print('[*] Downloading BinScope..')
    binscope_installer = urlrequest.urlopen(binscope_url)

    # Save content
    print(('[*] Saving to File {}'.format(binscope_installer_path)))

    # Write content to file
    binscope_installer_file.write(bytes(binscope_installer.read()))

    # Aaaand close
    binscope_installer_file.close()
    # Execute the installer
    print(('[*] Installing BinScope to {}'.format(binscope_path)))
    cmd = ('msiexec INSTALLLOCATION='
           '"{}" /i "{}" /passive'.format(
               binscope_path,
               binscope_installer_path))
    os.system(cmd)

    CONFIG['binscope']['file'] = binscope_path + '\\Binscope.exe'

    # Write to config
    with open(os.path.join(CONFIG_PATH, CONFIG_FILE), 'w') as configfile:
        CONFIG.write(configfile)  # pylint: disable-msg=E1101


def generate_secret():
    """Generate rsa keys for authentication."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
    print('[*] Generating secret, please hang on.')
    privkey = crypto_rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    priv_pem = privkey.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('utf-8')
    pub_pem = privkey.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1,
    ).decode('utf-8')

    # Save private and pub key
    priv_key_file = open(CONFIG['Vrika']['priv_key'], 'w')
    priv_key_file.write(priv_pem)
    priv_key_file.close()
    pub_key_file = open(CONFIG['Vrika']['pub_key'], 'w')
    pub_key_file.write(pub_pem)
    pub_key_file.close()
    config_path = os.path.join(
        expanduser('~'),
        '.Vrika',
        'config.py')
    print((
        '[!] Please move the private key file\n'
        '\t{}\n'
        '\tto Vrika to the path specified in {}\n'
        '\t(default: vrika-mobile-security/'
        'vrika_mobile_security/Vrika/windows_vm_priv_key.asc)'
        .format(CONFIG['Vrika']['priv_key'], config_path)
    ))
    input('Please press any key when done..')


def autostart():
    """Create the autostart binary and run it."""
    vrika_subdir_tools = CONFIG['Vrika']['tools']
    rpc_file = CONFIG['rpc']['file']
    autostart_file = CONFIG['autostart']['file']
    batch_file = AUTOSTART + autostart_file

    print('[*] Creating autostart binary...')

    # Open file
    autostart_file = open(batch_file, 'wb')

    # Define bat-text
    text = """
    @echo off
    python "{}" %*
    pause""".format(vrika_subdir_tools + rpc_file)
    autostart_file.write(bytes(text, 'utf8'))

    # Close handle
    autostart_file.close()

    print('[*] Done. Start the server.')

    # Execute. Beware the ' ' because of windows strange paths..
    os.system('"{}"'.format(batch_file))


def _place_lockfile(vrika_home):
    path = os.path.join(vrika_home, 'setup_done.txt')
    open(path, 'a').close()


def local_config():
    """Move local config and save paths."""
    # Set the CONFIG_PATH
    # Create path if it doesn't exist yet
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(CONFIG_PATH)

    # Copy predefined config to Vrika folder
    shutil.copy(
        os.getcwd() + '\\vrika_mobile_security\\install\\windows\\config.txt',
        os.path.join(CONFIG_PATH, CONFIG_FILE),
    )


def rewrite_local_config(vrika_home):
    """For local installation some config-vars need to be rewritten."""
    CONFIG['Vrika']['subdir_tools'] = (
        vrika_home
        + '\\vrika_mobile_security\\StaticAnalyzer\\tools\\windows\\')
    CONFIG['Vrika']['dir'] = vrika_home

    # Write to config
    with open(os.path.join(CONFIG_PATH, CONFIG_FILE), 'w') as configfile:
        CONFIG.write(configfile)  # pylint: disable-msg=E1101


def rewrite_config():
    """Rewrite the config to take the profile path as the base path."""
    # Take user path as base path
    CONFIG['Vrika']['dir'] = expanduser('~') + CONFIG['Vrika']['dir']

    # Rewrite config with new base path
    CONFIG['Vrika']['downloads'] = CONFIG['Vrika'][
        'dir'] + CONFIG['Vrika']['downloads']
    CONFIG['Vrika']['tools'] = CONFIG['Vrika'][
        'dir'] + CONFIG['Vrika']['tools']
    CONFIG['Vrika']['samples'] = CONFIG['Vrika'][
        'dir'] + CONFIG['Vrika']['samples']
    CONFIG['Vrika']['key_path'] = CONFIG['Vrika'][
        'dir'] + CONFIG['Vrika']['key_path']
    CONFIG['Vrika']['priv_key'] = CONFIG['Vrika'][
        'key_path'] + CONFIG['Vrika']['priv_key']
    CONFIG['Vrika']['pub_key'] = CONFIG['Vrika'][
        'key_path'] + CONFIG['Vrika']['pub_key']

    # Write to config
    with open(os.path.join(CONFIG_PATH, CONFIG_FILE), 'w') as configfile:
        CONFIG.write(configfile)  # pylint: disable-msg=E1101


def install_locally(vrika_home):
    """Install the Vrika-Utils on the same system as Vrika."""
    local_config()
    read_config()
    rewrite_config()
    create_folders()
    tools_nuget()
    tools_binskim()
    tools_binscope()
    _place_lockfile(vrika_home)


def _install_remote():
    """Install the Vrika-Utils on a Windows-VM for static analysis."""
    download_config()
    read_config()
    rewrite_config()
    create_folders()
    check_dependencies()
    tools_nuget()
    tools_binskim()
    tools_binscope()
    tools_rpcclient()
    generate_secret()
    autostart()


if __name__ == '__main__':
    # Gets directly run if setup.py is run on a remote machine
    _install_remote()
