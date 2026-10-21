#include "StageLighting.h"
#include "Endless.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/BillboardComponent.h"
#include "Components/LightComponent.h"
#include "Engine/Light.h"
#include "TimerManager.h"

AStageLighting::AStageLighting()
{
	RootComponent = CreateDefaultSubobject<UBillboardComponent>(TEXT("Icon"));
}

void AStageLighting::BeginPlay()
{
	Super::BeginPlay();

	if (Lights.IsEmpty())
	{
		for (TActorIterator<ALight> It(GetWorld()); It; ++It)
		{
			Lights.Add(*It);
		}
	}
	for (ALight* Light : Lights)
	{
		if (ULightComponent* Lamp = Light ? Light->GetLightComponent() : nullptr)
		{
			Lamps.Add(Lamp);
			BaseIntensity.Add(Lamp->Intensity);
			Lamp->SetUseTemperature(true);
		}
	}

	TActorIterator<ALoopManager> It(GetWorld());
	ALoopManager* Manager = It ? *It : nullptr;
	if (!Manager || Stages.IsEmpty())
	{
		UE_LOG(LogEndless, Error, TEXT("%s: needs a LoopManager in the level and at least one row in Stages"), *GetActorNameOrLabel());
		return;
	}
	Manager->OnStageStarted.AddDynamic(this, &AStageLighting::ApplyStage);
	ApplyStage(Manager->CurrentStage); // the manager may have started its first stage before we bound
}

void AStageLighting::ApplyStage(int32 Stage)
{
	const FStageLight& Row = Stages[FMath::Clamp(Stage, 0, Stages.Num() - 1)];
	StageIntensity = Row.Intensity;
	for (int32 i = 0; i < Lamps.Num(); ++i)
	{
		Lamps[i]->SetIntensity(BaseIntensity[i] * StageIntensity);
		Lamps[i]->SetTemperature(Row.Temperature);
	}

	// Spread the flickering lamps evenly over the list so they are not all in one room
	Flickering.Reset();
	const int32 Count = FMath::RoundToInt(Row.Flicker * Lamps.Num());
	for (int32 i = 0; i < Count; ++i)
	{
		Flickering.Add(i * Lamps.Num() / Count);
	}
	if (Flickering.IsEmpty())
	{
		GetWorldTimerManager().ClearTimer(FlickerTimer);
	}
	else
	{
		GetWorldTimerManager().SetTimer(FlickerTimer, this, &AStageLighting::FlickerTick, 0.08f, true);
	}
}

void AStageLighting::FlickerTick()
{
	for (int32 i : Flickering)
	{
		// Mostly on, sometimes a short dip: reads as a failing bulb, not a strobe
		const float Level = FMath::FRand() < 0.15f ? FMath::FRandRange(0.f, 0.3f) : 1.f;
		Lamps[i]->SetIntensity(BaseIntensity[i] * StageIntensity * Level);
	}
}
