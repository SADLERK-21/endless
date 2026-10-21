#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Anomaly.generated.h"

// One change of the apartment that lives on a range of loop stages and can grow stronger each stage.
// Simple case: fill ShowWhenActive / HideWhenActive with level actors (no scripting).
// Escalation: make a Blueprint child and implement OnStageChanged (Level 0 = first appearance, 1, 2... = stronger).
UCLASS(Blueprintable)
class ENDLESS_API AAnomaly : public AActor
{
	GENERATED_BODY()

public:
	AAnomaly();

	// First stage the anomaly appears on (stage 0 = normal apartment).
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Anomaly", meta = (ClampMin = 0))
	int32 FirstStage = 1;

	// Last stage it stays on. -1 = until the end.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Anomaly", meta = (ClampMin = -1))
	int32 LastStage = -1;

	// Actors that exist only while the anomaly is active.
	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Anomaly")
	TArray<TObjectPtr<AActor>> ShowWhenActive;

	// Actors that disappear while the anomaly is active (the normal version of a swapped object).
	UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Anomaly")
	TArray<TObjectPtr<AActor>> HideWhenActive;

	UPROPERTY(BlueprintReadOnly, Category = "Anomaly")
	bool bIsActive = false;

	UFUNCTION(BlueprintCallable, Category = "Anomaly")
	void SetAnomalyActive(bool bActive);

	void ApplyStage(int32 Stage);

	UFUNCTION(BlueprintImplementableEvent, Category = "Anomaly")
	void OnActiveChanged(bool bNowActive);

	// Called on every stage while active. Level = stages since FirstStage.
	UFUNCTION(BlueprintImplementableEvent, Category = "Anomaly")
	void OnStageChanged(int32 Stage, int32 Level);
};
