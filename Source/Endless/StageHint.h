#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StageHint.generated.h"

class ALoopManager;
class USoundBase;

// Helps a stuck player: place it in the room where the story item is. When the locked Stage repeats
// MinRepeat times without the objective, the Sound plays here every Interval seconds until the item is found.
// MinRepeat = 0 starts it with the stage itself: a ringing phone.
UCLASS()
class ENDLESS_API AStageHint : public AActor
{
	GENERATED_BODY()

public:
	AStageHint();

	UPROPERTY(EditAnywhere, Category = "Hint", meta = (ClampMin = 0))
	int32 Stage = 2;

	// Repeats of the stage before the hint starts. 1 = on the first repeat, 0 = as soon as the stage starts.
	UPROPERTY(EditAnywhere, Category = "Hint", meta = (ClampMin = 0))
	int32 MinRepeat = 2;

	UPROPERTY(EditAnywhere, Category = "Hint")
	TObjectPtr<USoundBase> Sound;

	UPROPERTY(EditAnywhere, Category = "Hint", meta = (ClampMin = 1))
	float Interval = 8.f;

	// Hook for stronger hints (light over the item...). RepeatCount grows each loop.
	UFUNCTION(BlueprintImplementableEvent, Category = "Hint")
	void OnHintStarted(int32 RepeatCount);

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void OnStageRepeated(int32 InStage, int32 RepeatCount);

	UFUNCTION()
	void OnStageStarted(int32 InStage);

	void StartHint();
	void PlayHint();

	UPROPERTY(Transient)
	TObjectPtr<ALoopManager> Manager;

	FTimerHandle Timer;
};
