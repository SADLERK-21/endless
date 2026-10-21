#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interactable.h"
#include "StoryItem.generated.h"

class ALoopManager;

// The story detail of a locked stage (photo, phone...). E on it completes the stage objective.
// Put it in an Anomaly's ShowWhenActive so it exists only on its stage.
UCLASS()
class ENDLESS_API AStoryItem : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	AStoryItem();

	// Hide the item after it was used (a photo taken). Off for things that stay (a phone hung up).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	bool bHideOnUse = true;

	// Shown on screen when used: a placeholder for the voiced or scripted story moment.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story", meta = (MultiLine = true))
	FText UseMessage;

	virtual void Interact_Implementation(AActor* Caller) override;

	// Hook for the story moment: sound, text, light change.
	UFUNCTION(BlueprintImplementableEvent, Category = "Story")
	void OnUsed();

protected:
	virtual void BeginPlay() override;

private:
	// Greybox look; swap the mesh in Details.
	UPROPERTY(VisibleAnywhere, Category = "Story")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(Transient)
	TObjectPtr<ALoopManager> Manager;

	bool bUsed = false; // a second E on an item that stays (the phone) does nothing
};
