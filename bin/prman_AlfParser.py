import pyparsing as pp
import re
import copy

class prman_AlfParser:
    def __init__(self):
        self.keywords = ['Job', 'Task', 'RemoteCmd']  

    def parseFile(self, fileText):
        commands = self.__parseCommandStructure(fileText, 0, isStart = True)
        #print(commands)
        textureCmds, Cmds, frames = self.extractCommandHierarchy(commands)
        return [textureCmds, Cmds, frames]

    def printCommands(self, cmds, currentIndent = 0):
        if isinstance(cmds, list):
            for e in cmds:
                self.printCommands(e, currentIndent + 1)
            
            print('---------------------')
        else:
            tabs = ''
            for i in range(currentIndent):
                tabs += '\t'
            print(tabs + repr(cmds))

    
    def __matchBracket(self, str):
        if str[0] != '{':
            return None
        num_open = 0
        for i, c in enumerate(str):
            if c == '{':
                num_open += 1
            elif c == '}':
                num_open -= 1
            
            if num_open == 0:
                return str[1:i]
        return None
    
    def leadingSpace(self, text):
        return len(text) - len(text.lstrip())
    
    def removingLeadingNewLines(self, text):
        return text.lstrip('\n')


    def determineCommandLength(self, text):
        if text[0] == '\n':
            raise ValueError('Determine command length should never take newline as first char!')
        text = copy.deepcopy(text)
        lines = text.split('\n')
        lengths = [len(l) for l in lines]
        currentIndent = self.leadingSpace(lines[0])
        extent = len(lines[0])
        for i, l in enumerate(lines[1:]):
            if self.leadingSpace(l) != currentIndent:
                extent += lengths[i + 1] + 1
            else:
                extent += lengths[i + 1] + 1
                return extent
        return extent

    def extractAllArgs(self, text):
        currentIndent = 0
        parsingBracket = False
        parsingSimple = False
        args = []
        argNames = []
        resultText = ''
        currentBracketText = ''
        i = 0
        while i < len(text):
            if parsingBracket:
                #process indents
                if text[i] == '}':
                    currentIndent -= 1
                    currentBracketText += text[i]
                    if currentIndent == 0:
                        args.append(currentBracketText[1:-1])
                        currentBracketText = ''
                        parsingBracket = False
                        currentIndent = 0
                elif text[i] == '{':
                    currentBracketText += text[i]
                    currentIndent += 1
                else:
                    currentBracketText += text[i]
            elif parsingSimple:
                if text[i] == ' ':
                    args.append(currentBracketText  )
                    currentBracketText = ''
                    parsingSimple = False
                else:
                    currentBracketText += text[i]
            else:
                if text[i] == '-':
                    counter = 1
                    argName = ''
                    while True:
                        if text[i + counter] == ' ':
                            argNames.append(argName)
                            if text[i + counter + 1] == '{':
                                currentIndent = 0
                                parsingBracket = True
                                i = i + counter
                            else:
                                parsingSimple = True
                                i = i + counter
                            break
                        else:
                            argName += text[i + counter]
                            counter += 1
            i += 1
        
        return argNames, args, resultText

    def parseOptions(self, text):
        optsNames, opts, textWithoutOpts = self.extractAllArgs(text)
        result = {}
        for i in range(len(optsNames)):
            result[optsNames[i]] = opts[i]
        
        return result

    def parseJob(self, text):
        newJob = self.parseOptions(text)
        newJob['type'] = 'job'
        return newJob
    
    def parseRemoteCmd(self, text):
        #grab the actual command
        i = len(text) - 1
        actualCommand = ''
        while i > 0:
            if text[i] == '}':
                break
            else:
                i -= 1
        while i > 0:
            if  text[i] == '{':
                actualCommand = text[i] + actualCommand
                break
            else:
                actualCommand = text[i] + actualCommand
                i -=1
        
        newCmd = self.parseOptions(text[:i])
        newCmd['type'] = 'remoteCommand'
        newCmd['command'] = actualCommand[1:-1]
        return newCmd

    def parseTask(self, text):
        #parse Task Name
        taskName = ''
        start = text.find('{') + 1
        for i in range(start, len(text)):
            if text[i] == '}':
                break
            else:
                taskName += text[i]
        text = text[i+1:]
        newTask = self.parseOptions(text)
        newTask['type'] = 'task'
        newTask['taskName'] = taskName
        return newTask

    def __parseCommandStructure(self, text, indentLevel, isStart = False):
        structure = []
        text = copy.deepcopy(text)
        if isStart:
            text = text[17:]
        starts = [text.find(k) for k in self.keywords]
        for i in range(len(starts)):
            if starts[i] < 0:
                starts[i] = 111111111111111111
        lowestStartIdx = starts.index(min(starts))

        #move back until new line
        startIdx = starts[lowestStartIdx]

        if startIdx == 111111111111111111:
            return None
        while startIdx > 0:
            if text[startIdx - 1] == '\t':
                startIdx -= 1
            else:
                break
        if lowestStartIdx == 0: #Job
            length = self.determineCommandLength(text[startIdx:])
            newItem = self.parseJob(text[startIdx+3:startIdx+length])
        elif lowestStartIdx == 1: #Task
            length = self.determineCommandLength(text[startIdx:])
            newItem = self.parseTask(text[startIdx+4:startIdx+length])
        elif lowestStartIdx == 2: #RemoteCmd
            length = self.determineCommandLength(text[startIdx:])
            newItem = self.parseRemoteCmd(text[startIdx+9:startIdx+length])

        try: #why does hasattr not work here?
            #print('Attempting to parse subtasks')
            newItem['subtasks'] = self.__parseCommandStructure(self.removingLeadingNewLines(newItem['subtasks']), indentLevel+1)
        except:
            pass
        try:
            newItem['cmds'] = self.__parseCommandStructure(self.removingLeadingNewLines(newItem['cmds']), indentLevel+1)
        except:
            pass
        structure.append(newItem)

        nextCommands = self.__parseCommandStructure(text[startIdx+length:], indentLevel)
        if nextCommands:
            for c in nextCommands:
                structure.append(c)
        return structure

    def extractCommandsForFrame(self, task):
        frames = []
        cmds = {}
        for t in task['subtasks']:
            subcmds = []
            #extract frame index
            frameLinearIdx = int(t['taskName'].replace('Frame', ''))
            frames.append(frameLinearIdx)
            for t_sub in t['subtasks']:
                try:
                    for c in t_sub['cmds']:
                        subcmds.append(c)
                except:
                    pass
            if subcmds:
                cmds[str(frameLinearIdx)] = subcmds
        return cmds, frames

    def extractCommandsForTexture(self, task):
        cmds = []
        for t in task['subtasks']:
            try:
                for c in t['cmds']:
                    cmds.append(c)
            except:
                pass
        return cmds
    
    def extractCommandHierarchy(self, jobs):
        textureCommands = []
        commands = {}
        for j in jobs:
            for t in j['subtasks']:
                #get all texture conversion tasks
                if t['taskName'] == 'Job Textures': 
                    try:
                        newCommands = self.extractCommandsForTexture(t)
                        #textureCommands.append(newCommands)
                        for c in newCommands:
                            textureCommands.append(c)
                    except:
                        pass
                #get commands for all frames
                else:
                    newCommands, frames = self.extractCommandsForFrame(t)
                    commands = {**commands, **newCommands}

        return textureCommands, commands, frames
    
def main():
    with open('data/blue/shots/spool.alf', 'r') as myfile:
        data = myfile.read()
    parser = prman_AlfParser()
    textureCmds, Cmds, frames = parser.parseFile(data)
    print('Frames: ', frames)

if __name__ == "__main__":
    main()