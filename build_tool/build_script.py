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

outputFilename = 'hello_world.exe'

configCacheVars = {}

# Debug cmake generate cache vars
configCacheVars['dbg'] = [
]
# Release cmake generate cache vars
configCacheVars['rel'] = [
]
# ReleaseWithDebugInfo cmake generate cache vars
configCacheVars['rwd'] = [
]

# =================================================================================================
# Preferences:

enableCompletionSound = True

cmakeGeneratorsDict = {}
cmakeGeneratorsDict['default'] = ''
cmakeGeneratorsDict['vs'] = '-G Visual Studio 17 2022'
cmakeGeneratorsDict['nm'] = '-G Ninja Multi-Config'

configShorthands = {}
configShorthands['dbg'] = 'Debug'
configShorthands['rel'] = 'Release'
configShorthands['rwd'] = 'Release'

buildOperations = {}
buildOperations['g'] = 'generate'
buildOperations['b'] = 'build'
buildOperations['d'] = 'deploy'
buildOperations['r'] = 'run'
buildOperations['c'] = 'clean'
buildOperations['o'] = 'open in ide'

outputModes = {}
outputModes[''] = 'both to file'
outputModes['o'] = 'stdout to console'
outputModes['e'] = 'stderr to console'
outputModes['oe'] = 'both to console'
outputModes['eo'] = 'both to console'

redirOutputDir = '/stdOutput'
generateStdOut = redirOutputDir + '/generateStdOut.txt'
generateStdErr = redirOutputDir + '/generateStdErr.txt'
buildStdOut = redirOutputDir + '/buildStdOut.txt'
buildStdErr = redirOutputDir + '/buildStdErr.txt'
deployStdOut = redirOutputDir + '/deployStdOut.txt'
deployStdErr = redirOutputDir + '/deployStdErr.txt'
runStdOut = redirOutputDir + '/runStdOut.txt'
runStdErr = redirOutputDir + '/runStdErr.txt'

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

def printArg1info(infoStr):
    print(bcolors.GREEN + 'Available generators are:' + bcolors.NORMAL)
    print(bcolors.GREEN + infoStr + bcolors.NORMAL)
def printArg2info(infoStr):
    print(bcolors.YELLOW + 'Available configurations are:' + bcolors.NORMAL)
    print(bcolors.YELLOW + infoStr + bcolors.NORMAL)
def printArg3info(infoStr):
    print(bcolors.BLUE + 'Available build operations are:' + bcolors.NORMAL)
    print(bcolors.BLUE + infoStr + bcolors.NORMAL)
    print(bcolors.BLUE + 'FYI - concat multiple OK (ie cgbd)' + bcolors.NORMAL)
def printArg4info(infoStr):
    print(bcolors.YELLOW + '(optional) Available output modes are:' + bcolors.NORMAL)
    print(bcolors.YELLOW + infoStr + bcolors.NORMAL)

if len(sys.argv) < 4 or len(sys.argv) > 5:
    printArg1info(str(cmakeGeneratorsDict))
    printArg2info(str(configShorthands))
    printArg3info(str(buildOperations))
    printArg4info(str(outputModes))
    sys.exit('Enter either 3 or 4 args.')

# arg 1
buildGenerator = sys.argv[1]
if (buildGenerator in cmakeGeneratorsDict.keys()) == False:
    printArg1info(str(cmakeGeneratorsDict))
    sys.exit(bcolors.RED + 'Error - Bad generator arg' + bcolors.NORMAL)

# arg 2
buildConfig = sys.argv[2]
if (buildConfig in configShorthands.keys()) == False:
    printArg2info(str(configShorthands))
    sys.exit(bcolors.RED + 'Error - Bad config arg' + bcolors.NORMAL)

# arg 3
buildOperation = sys.argv[3]
for element in range(0, len(buildOperation)):
    if (buildOperation[element] in buildOperations.keys()) == False:
        printArg3info(str(buildOperations))
        sys.exit(bcolors.RED + 'Error - Bad build operation arg' + bcolors.NORMAL)
        break
    
# arg 4 (optional)
outputMode = 'default'
if len(sys.argv) == 5:
    outputMode = sys.argv[4]
    if (outputMode in outputModes.keys()) == False:
        printArg4info(str(outputModes))
        sys.exit(bcolors.RED + 'Error - Bad output mode arg' + bcolors.NORMAL)

# the full path to the parent dir of this file
commandsDirPath = os.path.realpath(os.path.dirname(__file__)).replace(os.sep, '/')

# output folder for the generated cmake project
outputFolder = 'build/' + buildGenerator + '_' + buildConfig

def create_redirOutputDirs():
    os.makedirs(outputFolder + redirOutputDir, exist_ok=True)

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

    if outputMode == 'o' or outputMode == 'oe' or outputMode == 'eo':
        file_stdOut = None # to console
        print(bcolors.GREEN + 'std out going to console.' + bcolors.NORMAL)
    else:
        print('Sending stdout to ' + stdOut_filename)
    if outputMode == 'e' or outputMode == 'oe' or outputMode == 'eo':
        file_stdErr = None # to console
        print(bcolors.RED + 'std err going to console.' + bcolors.NORMAL)
    else:
        print('Sending stderr to ' + stdErr_filename)

# =================================================================================================
def generate():
    global file_stdOut
    global file_stdErr
    create_redirOutputDirs()

    print(bcolors.GREEN + 'Generating...' + bcolors.NORMAL)
    genStart = time.time()

    redirect_output(generateStdOut, generateStdErr)

    subprocess.call([
        'cmake',
        '-S', '.',
        '-B', outputFolder,
        cmakeGeneratorsDict[buildGenerator],
        ] + configCacheVars[buildConfig]
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
    create_redirOutputDirs()
    
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
    create_redirOutputDirs()

    print(bcolors.CYAN + 'Deploying...' + bcolors.NORMAL)

    redirect_output(deployStdOut, deployStdErr)
    configStr = configShorthands[buildConfig]

    exePath = outputFolder + '/' + configStr + '/' + outputFilename
    exePath = os.path.realpath(exePath).replace(os.sep, '/')
    
    os.makedirs(setup.deployLocation + '/' + buildConfig, exist_ok=True)

    # shutil.copyfile(exePath, setup.deployLocation + '/' + buildConfig)

    # windows specific example using robocopy:
    if os.path.isfile(exePath) :
        subprocess.call([
            'robocopy', '/S','/NP','/NFL',
            outputFolder,
            setup.deployLocation + '/' + buildConfig,
            outputFilename
        ], stdout=file_stdOut, stderr=file_stdErr)
        # print('Exe was located at ' + exePath)
    else:
        print('No exe found at ' + exePath)

    # if enableCompletionSound == True:
    #     winsound.Beep(784, 500) # Hz - G5, 500 ms


# =================================================================================================
def run():
    global file_stdOut
    global file_stdErr
    create_redirOutputDirs()

    print(bcolors.CYAN + 'Running...' + bcolors.NORMAL)

    redirect_output(runStdOut, runStdErr)
    configStr = configShorthands[buildConfig]

    exePath = outputFolder + '/' + configStr + '/' + outputFilename
    exePath = os.path.realpath(exePath).replace(os.sep, '/')
    
    os.makedirs(setup.deployLocation + '/' + buildConfig, exist_ok=True)
    
    exePath = outputFolder + '/' + configStr + '/' + outputFilename
    exePath = os.path.realpath(exePath).replace(os.sep, '/')
    if os.path.isfile(exePath) :
        subprocess.call([
            exePath
        ], stdout=file_stdOut, stderr=file_stdErr)
    else:
        print('No exe found at ' + exePath)

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
def open_ide():
    
    if os.path.exists(outputFolder):
        shutil.rmtree( outputFolder, onerror = remove_readonly )
        print(bcolors.YELLOW + 'Opening...' + outputFolder + bcolors.NORMAL)
    else:
        print('Nothing to open...' + outputFolder + ' does not exist.')
        
    subprocess.call([
        'cmake','--open',outputFolder
    ])
    
# =================================================================================================
for element in range(0, len(buildOperation)):
    if buildOperation[element] == 'g':
        generate()
    elif buildOperation[element] == 'b':
        build()
    elif buildOperation[element] == 'd':
        deploy()
    elif buildOperation[element] == 'r':
        run()
    elif buildOperation[element] == 'c':
        clean()
    elif buildOperation[element] == 'o':
        open_ide()

