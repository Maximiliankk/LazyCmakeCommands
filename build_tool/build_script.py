# The goal of this script is to make building and deploying as close as possible to a 1-click operation.

# It is recommended to commit only the default usage of this file to your repo.
# After the default usage is committed, then add this file to .gitignore to prevent further tracking.
# Later changes to the default usage can be committed with 'git add --force -- file1 file2'

import os.path
import time
import subprocess
import sys
import shutil
import stat
import setup

# windows-specific features:
# import winsound

outputFilename = 'yourapp.exe'

# Debug cmake generate cache vars
DBG_CacheVars = [
]
# Release cmake generate cache vars
REL_CacheVars = [
]
# ReleaseWithDebugInfo cmake generate cache vars
RWD_CacheVars = [
]

# =================================================================================================
# Preferences:

enableCompletionSound = True

# Optionally redirect stdout and stderr to file
enableStdoutToFile = True
enableStderrToFile = False
redirOutputDir = '/stdOutput'
generateStdOut = redirOutputDir + '/generateStdOut.txt'
generateStdErr = redirOutputDir + '/generateStdErr.txt'
buildStdOut = redirOutputDir + '/buildStdOut.txt'
buildStdErr = redirOutputDir + '/buildStdErr.txt'
deployStdOut = redirOutputDir + '/deployStdOut.txt'
deployStdErr = redirOutputDir + '/deployStdErr.txt'

cmakeGeneratorsDict = {}
cmakeGeneratorsDict['default'] = ''
cmakeGeneratorsDict['vs'] = '-G Visual Studio 17 2022'
cmakeGeneratorsDict['nm'] = '-G Ninja Multi-Config'

buildOperations = {}
buildOperations['g'] = 'generate'
buildOperations['b'] = 'build'
buildOperations['d'] = 'deploy'
buildOperations['c'] = 'clean'

configShorthands = {}
configShorthands['dbg'] = 'Debug'
configShorthands['rel'] = 'Release'
configShorthands['rwd'] = 'Release'

# end of preferences
# =================================================================================================

# =================================================================================================
# args handling

# ANSI escape sequences for colored console output
class bcolors:
    NORMAL = '\033[0m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    
if len(sys.argv) != 4:
    sys.exit('Error - need exactly 3 args.')

# arg 1
buildGenerator = sys.argv[1]
if (buildGenerator in cmakeGeneratorsDict.keys()) == False:
    print(bcolors.GREEN + 'Available generators are:' + bcolors.NORMAL)
    print(bcolors.GREEN + str(cmakeGeneratorsDict) + bcolors.NORMAL) 
    sys.exit(bcolors.RED + 'Error - Bad generator arg' + bcolors.NORMAL)

# arg 2
buildConfig = sys.argv[2]
if (buildConfig in configShorthands.keys()) == False:
    print(bcolors.GREEN + 'Available configurations are:' + bcolors.NORMAL)
    print(bcolors.GREEN + str(configShorthands) + bcolors.NORMAL) 
    sys.exit(bcolors.RED + 'Error - Bad config arg' + bcolors.NORMAL)

# arg 3
buildOperation = sys.argv[3]
if (buildOperation in buildOperations.keys()) == False:
    print(bcolors.GREEN + 'Available build operations are:' + bcolors.NORMAL)
    print(bcolors.GREEN + str(buildOperations) + bcolors.NORMAL) 
    sys.exit(bcolors.RED + 'Error - Bad build operation arg' + bcolors.NORMAL)

# the full path to the parent dir of this file
commandsDirPath = os.path.realpath(os.path.dirname(__file__)).replace(os.sep, '/')

# output folder for the generated cmake project
outputFolder = 'build/' + buildGenerator + '_' + buildConfig

if not os.path.exists('build/'):
    print('No ' + 'build/')
    print('Creating... ')
    os.mkdir('build/')
if not os.path.exists(outputFolder):
    print('No ' + outputFolder)
    print('Creating... ')
    os.mkdir(outputFolder)
if not os.path.exists(outputFolder + redirOutputDir):
    print('No ' + outputFolder + redirOutputDir)
    print('Creating... ')
    os.mkdir(outputFolder + redirOutputDir)

# end of args handling
# =================================================================================================

# print colored number if value is low, med, or high
def print_low_med_high(value, low, med) -> str:
    if value < low:
        return bcolors.GREEN + str(value) + bcolors.NORMAL
    elif value < med:
        return bcolors.YELLOW + str(value) + bcolors.NORMAL
    else: # high
        return bcolors.RED + str(value) + bcolors.NORMAL

file_stdOut = ''
file_stdErr = ''
def redirect_output(stdoutFile, stderrFile):
    global file_stdOut
    global file_stdErr
    stdOut_filename = outputFolder + stdoutFile
    stdErr_filename = outputFolder + stderrFile
    file_stdOut = open(stdOut_filename, 'w')
    file_stdErr = open(stdErr_filename, 'w')
    if enableStdoutToFile == False:
        file_stdOut = None
    else:
        print('Sending stdout to ' + stdOut_filename)
    if enableStderrToFile == False:
        file_stdErr = None
    else:
        print('Sending stderr to ' + stdOut_filename)

# =================================================================================================
def generate():
    global file_stdOut
    global file_stdErr

    print(bcolors.GREEN + 'Generating...' + bcolors.NORMAL)
    genStart = time.time()

    redirect_output(generateStdOut, generateStdErr)

    subprocess.call([
        'cmake',
        '-S', '.',
        '-B', outputFolder,
        cmakeGeneratorsDict[buildGenerator],
        ] + DBG_CacheVars
    , stdout=file_stdOut, stderr=file_stdErr)

    executionTime = (time.time() - genStart)
    print('Generate time: ' + str(round(executionTime,2)) + ' sec ('
        + print_low_med_high(round(executionTime / 60, 2),1,10)
        + ' min)')
    # if enableCompletionSound == True:
    #     winsound.Beep(523, 500) # Hz - C5, 500 ms
    print('generate complete...')

# =================================================================================================
def build():
    global file_stdOut
    global file_stdErr
    
    print(bcolors.BLUE + 'Building...' + bcolors.NORMAL)
    buildStart = time.time()

    redirect_output(buildStdOut, buildStdErr)
    configStr = configShorthands[buildConfig]

    subprocess.call([
        'cmake',
        '--build', outputFolder,
        '--config', configStr
    ], stdout=file_stdOut, stderr=file_stdErr)

    executionTime = (time.time() - buildStart)
    print('Build time: ' + str(round(executionTime,2)) + ' sec ('
        + print_low_med_high(round(executionTime / 60, 2),1,10)
        + ' min)')
    # if enableCompletionSound == True:
    #     winsound.Beep(659, 500) # Hz - B5, 500 ms

# =================================================================================================
def deploy():
    global file_stdOut
    global file_stdErr

    print(bcolors.CYAN + 'Deploying...' + bcolors.NORMAL)

    redirect_output(deployStdOut, buildStdErr)
    configStr = configShorthands[buildConfig]

    # windows specific example using robocopy:

    # exePath = outputFolder + '/' + configStr + '/' + outputFilename
    # exePath = os.path.realpath(exePath).replace(os.sep, '/')
    # if os.path.isfile(exePath) :
    #     subprocess.call([
    #         'robocopy', '/S','/NP','/NFL',
    #         outputFolder,
    #         setup.deployLocation + '/' + buildConfig,
    #         outputFilename
    #     ], stdout=file_stdOut, stderr=file_stdErr)
    #     print('Exe was located at ' + exePath)
    # else:
    #     print('No exe found at ' + exePath)

    # if enableCompletionSound == True:
    #     winsound.Beep(784, 500) # Hz - G5, 500 ms

# =================================================================================================
def clean():

    print('Going to clean...' + outputFolder + '...')

    # recursively remove read-only from any file in the build folder
    # otherwise it might not clean properly
    def remove_readonly(fn, path, excinfo):
        try:
            os.chmod(path, stat.S_IWRITE)
            fn(path)
        except Exception as exc:
            print("Skipped:", path, "because:\n", exc)

    if os.path.exists(outputFolder):
        shutil.rmtree( outputFolder, onerror = remove_readonly )
        print(bcolors.YELLOW + 'Cleaned...' + outputFolder + bcolors.NORMAL)
    else:
        print('Nothing to clean...' + outputFolder + ' does not exist.')

# =================================================================================================
if buildOperation == 'g':
    generate()
elif buildOperation == 'b':
    build()
elif buildOperation == 'd':
    deploy()
elif buildOperation == 'c':
    clean()