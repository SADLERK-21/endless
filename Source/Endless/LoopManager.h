#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LoopManager.generated.h"

class AAnomaly;
class ALoopExit;
class UArrowComponent;

USTRUCT(BlueprintType)
struct FLoopStage
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loop")
	FName Name;

	// What the player should feel / learn on this stage. For the designer, not shown in game.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loop", meta = (MultiLine = true))
	FText DesignNote;

	// The loop repeats this stage until CompleteObjective() is called (note found, phone answered...).
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loop")
	bool bRequiresObjective = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnStageStarted, int32, Stage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnStageRepeated, int32, Stage, int32, RepeatCount);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLoopFinale);

// Place ONE per level, on the floor by the bed: the player wakes up here, facing the arrow, at the start of every loop.
// Each pass through the LoopExit fades to black, moves the apartment to the next stage (or repeats it, see bRequiresObjective)
// and wakes the player up again.
// Anomalies decide by themselves on which stages they exist (AAnomaly::FirstStage / LastStage).
UCLASS()
class ENDLESS_API ALoopManager : public AActor
{
	GENERATED_BODY()

public:
	ALoopManager();

	// Stage 0 = the normal apartment. The finale fires after passing the exit on the last stage.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Loop")
	TArray<FLoopStage> Stages;

	UPROPERTY(BlueprintReadOnly, Category = "Loop")
	int32 CurrentStage = 0;

	// Times the current stage repeated without the objective. Use it for escalating hints.
	UPROPERTY(BlueprintReadOnly, Category = "Loop")
	int32 RepeatCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Loop")
	bool bObjectiveDone = false;

	// Seconds from stepping out of the front door to full black.
	UPROPERTY(EditAnywhere, Category = "Loop", meta = (ClampMin = 0.1))
	float FadeOutTime = 0.1f;

	// Seconds from black to waking up by the bed. Short = jolting awake from a nightmare.
	UPROPERTY(EditAnywhere, Category = "Loop", meta = (ClampMin = 0.1))
	float WakeUpTime = 0.4f;

	// Testing: begin play on this stage instead of 0.
	UPROPERTY(EditAnywhere, Category = "Loop|Debug", meta = (ClampMin = 0))
	int32 DebugStartStage = 0;

	// Prints the stage on screen. Development builds only.
	UPROPERTY(EditAnywhere, Category = "Loop|Debug")
	bool bDebugShowStage = false;

	// Bind in Level Blueprint: scripted events, lighting changes, sounds.
	UPROPERTY(BlueprintAssignable, Category = "Loop")
	FOnStageStarted OnStageStarted;

	UPROPERTY(BlueprintAssignable, Category = "Loop")
	FOnStageRepeated OnStageRepeated;

	UPROPERTY(BlueprintAssignable, Category = "Loop")
	FOnLoopFinale OnFinale;

	// Call from Blueprint when the player found the story detail of this stage.
	UFUNCTION(BlueprintCallable, Category = "Loop")
	void CompleteObjective();

	void HandleExit(ALoopExit* Exit, APawn* Pawn);

protected:
	virtual void BeginPlay() override;

private:
	void EnterStage(int32 Stage);
	void WakeUp(TWeakObjectPtr<APawn> Pawn);

	UPROPERTY(VisibleAnywhere, Category = "Loop")
	TObjectPtr<UArrowComponent> Arrow;

	UPROPERTY(Transient) TArray<TObjectPtr<AAnomaly>> Anomalies;

	bool bFinished = false;
	bool bTransitioning = false; // screen is fading, ignore the exit trigger
};
