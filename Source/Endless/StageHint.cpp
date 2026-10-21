#include "StageHint.h"
#include "Endless.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/BillboardComponent.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

AStageHint::AStageHint()
{
	RootComponent = CreateDefaultSubobject<UBillboardComponent>(TEXT("Icon"));
}

void AStageHint::BeginPlay()
{
	Super::BeginPlay();

	TActorIterator<ALoopManager> It(GetWorld());
	Manager = It ? *It : nullptr;
	if (!Manager)
	{
		UE_LOG(LogEndless, Error, TEXT("%s: no LoopManager in level"), *GetActorNameOrLabel());
		return;
	}
	Manager->OnStageRepeated.AddDynamic(this, &AStageHint::OnStageRepeated);
	Manager->OnStageStarted.AddDynamic(this, &AStageHint::OnStageStarted);
}

void AStageHint::OnStageRepeated(int32 InStage, int32 RepeatCount)
{
	if (InStage != Stage || RepeatCount < MinRepeat)
	{
		return;
	}
	OnHintStarted(RepeatCount);
	if (!GetWorldTimerManager().IsTimerActive(Timer))
	{
		GetWorldTimerManager().SetTimer(Timer, this, &AStageHint::PlayHint, Interval, true, 1.f); // first one right after waking up
	}
}

void AStageHint::OnStageStarted(int32 InStage)
{
	GetWorldTimerManager().ClearTimer(Timer);
}

void AStageHint::PlayHint()
{
	if (Manager->bObjectiveDone)
	{
		GetWorldTimerManager().ClearTimer(Timer);
		return;
	}
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation());
	}
#if !UE_BUILD_SHIPPING
	else if (GEngine)
	{
		// shortcut: no hint sounds yet, the placeholder is a debug line; assign Sound in Details in week 5
		GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Yellow, FString::Printf(TEXT("[hint sound] %s"), *GetActorNameOrLabel()));
	}
#endif
}
