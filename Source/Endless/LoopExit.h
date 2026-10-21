#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LoopExit.generated.h"

class UBoxComponent;
class UArrowComponent;
class ALoopManager;

// Trigger just outside the front door: stepping into it ends the loop. Pivot sits on the floor.
UCLASS()
class ENDLESS_API ALoopExit : public AActor
{
	GENERATED_BODY()

public:
	ALoopExit();

	// Optional: found automatically if the level has one LoopManager.
	UPROPERTY(EditInstanceOnly, Category = "Loop")
	TObjectPtr<ALoopManager> Manager;

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void OnBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
		int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, Category = "Loop")
	TObjectPtr<UBoxComponent> Box;

	UPROPERTY(VisibleAnywhere, Category = "Loop")
	TObjectPtr<UArrowComponent> Arrow;
};
