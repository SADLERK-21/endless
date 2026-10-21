#include "EndlessGameMode.h"
#include "EndlessCharacter.h"

AEndlessGameMode::AEndlessGameMode()
{
	// Make BP_GameMode as a child and point this at BP_Player to tune the player in the editor.
	DefaultPawnClass = AEndlessCharacter::StaticClass();
}
