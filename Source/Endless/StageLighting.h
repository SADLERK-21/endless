#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StageLighting.generated.h"

class ALight;
class ALoopManager;
class ULightComponent;

USTRUCT(BlueprintType)
struct FStageLight
{
	GENERATED_BODY()

	// Multiplier of each lamp's own intensity set in the level.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Lighting", meta = (ClampMin = 0))
	float Intensity = 1.f;

	// Kelvin: 2700 = warm home lamp, 6500 = cold white.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Lighting", meta = (ClampMin = 1700, ClampMax = 12000))
	float Temperature = 2700.f;

	// Share of lamps that flicker, 0..1.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Lighting", meta = (ClampMin = 0, ClampMax = 1))
	float Flicker = 0.f;
};

// Rough per-stage light script: one row per loop stage, applied to the lamps when the stage starts.
// Lamps must be Movable. Fine lighting per stage comes later (MVP week 4).
UCLASS()
class ENDLESS_API AStageLighting : public AActor
{
	GENERATED_BODY()

public:
	AStageLighting();

	// Index = stage. Stages past the end use the last row.
	UPROPERTY(EditAnywhere, Category = "Lighting")
	TArray<FStageLight> Stages;

	// Lamps to drive. Empty = every light in the level.
	UPROPERTY(EditInstanceOnly, Category = "Lighting")
	TArray<TObjectPtr<ALight>> Lights;

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void ApplyStage(int32 Stage);

	void FlickerTick();

	UPROPERTY(Transient)
	TArray<TObjectPtr<ULightComponent>> Lamps;

	TArray<float> BaseIntensity; // per lamp, as set in the level
	TArray<int32> Flickering;    // indices into Lamps
	float StageIntensity = 1.f;
	FTimerHandle FlickerTimer;
};
