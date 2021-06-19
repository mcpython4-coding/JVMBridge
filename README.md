# JVMBridge
Repository containing code for a JVM implementation in python

Contains code for interacting with mcpython-4, which is optional
Can be used without the "runtime" module for only loading java bytecode

bridge contains bridge code between mcpython-4 and the java code
builtin contains the common code of the standard library

WARNING: As this is a VM interacting with your computer loading arbitrary code,
Code you are loading may be malicious. Run code on your own risk

# How-To install
General speaking, you have to provide the correct version of the jvm code published together
with the general code and link it somehow. This can be done simply by putting the jvm folder in the same folder
as the code of the game. The game will automatically load if it is in the right place.

In theory, you could also pack it into some other folders looked up by the python installation,
like the library folders.
