// Native helper for isolated MediaPlayer scaling experiments.
// Does not touch the active settings file: caller supplies distinct paths.
#include <File.h>
#include <Message.h>
#include <stdio.h>
#include <string.h>

static status_t
Load(const char* path, BMessage& message)
{
	BFile input(path, B_READ_ONLY);
	status_t result = input.InitCheck();
	return result == B_OK ? message.Unflatten(&input) : result;
}

int
main(int argc, char** argv)
{
	if (argc != 2 && argc != 4)
		return 2;
	BMessage message;
	if (Load(argv[1], message) != B_OK)
		return 3;
	bool value = true;
	status_t result = message.FindBool("scaleBilinear", &value);
	if (result != B_OK && result != B_NAME_NOT_FOUND)
		return 4;
	if (argc == 2) {
		printf("scaleBilinear=%d\n", value ? 1 : 0);
		return 0;
	}
	if (strcmp(argv[1], argv[2]) == 0
		|| (strcmp(argv[3], "on") != 0 && strcmp(argv[3], "off") != 0))
		return 2;
	value = strcmp(argv[3], "on") == 0;
	result = result == B_NAME_NOT_FOUND
		? message.AddBool("scaleBilinear", value)
		: message.ReplaceBool("scaleBilinear", value);
	if (result != B_OK)
		return 4;
	{
		BFile output(argv[2], B_WRITE_ONLY | B_CREATE_FILE | B_FAIL_IF_EXISTS);
		if (output.InitCheck() != B_OK || message.Flatten(&output) != B_OK)
			return 5;
	}
	BMessage verify;
	bool actual;
	if (Load(argv[2], verify) != B_OK
		|| verify.FindBool("scaleBilinear", &actual) != B_OK
		|| actual != value)
		return 6;
	printf("scaleBilinear=%d\n", actual ? 1 : 0);
	return 0;
}
