#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interactable.h"
#include "LoopDoor.generated.h"

class ALoopManager;

// Door the player opens and closes with E. Pivot = hinge on the floor, the panel extends along the arrow's right (+Y).
// Closes itself on every new loop, so it is shut again when the player wakes up.
UCLASS()
class ENDLESS_API ALoopDoor : public AActor, public IInteractable
{
	GENERATED_BODY()

public:
	ALoopDoor();

	// Negative = opens the other way.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	float OpenAngle = 95.f;

	// Degrees per second.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = 1))
	float OpenSpeed = 110.f;

	virtual void Interact_Implementation(AActor* Caller) override;

	UFUNCTION(BlueprintCallable, Category = "Door")
	void SetOpen(bool bOpen, bool bInstant = false);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UFUNCTION()
	void OnStageStarted(int32 Stage);

	UFUNCTION()
	void OnStageRepeated(int32 Stage, int32 RepeatCount);

	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<USceneComponent> Hinge;

	UPROPERTY(VisibleAnywhere, Category = "Door")
	TObjectPtr<UStaticMeshComponent> Panel;

	float TargetYaw = 0.f;
};
