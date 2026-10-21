#include "Anomaly.h"

AAnomaly::AAnomaly()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AAnomaly::SetAnomalyActive(bool bActive)
{
	bIsActive = bActive;

	auto SetShown = [](AActor* Actor, bool bShown)
	{
		if (Actor)
		{
			Actor->SetActorHiddenInGame(!bShown);
			Actor->SetActorEnableCollision(bShown);
		}
	};
	for (AActor* Actor : ShowWhenActive) { SetShown(Actor, bActive); }
	for (AActor* Actor : HideWhenActive) { SetShown(Actor, !bActive); }

	OnActiveChanged(bActive);
}

void AAnomaly::ApplyStage(int32 Stage)
{
	const bool bShouldBeActive = Stage >= FirstStage && (LastStage < 0 || Stage <= LastStage);
	if (bShouldBeActive != bIsActive)
	{
		SetAnomalyActive(bShouldBeActive);
	}
	if (bShouldBeActive)
	{
		OnStageChanged(Stage, Stage - FirstStage);
	}
}
