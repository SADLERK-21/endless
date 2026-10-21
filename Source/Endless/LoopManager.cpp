#include "LoopManager.h"
#include "Endless.h"
#include "Anomaly.h"
#include "LoopExit.h"
#include "EngineUtils.h"
#include "Components/ArrowComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "TimerManager.h"
#include "Engine/Engine.h"

ALoopManager::ALoopManager()
{
	Arrow = CreateDefaultSubobject<UArrowComponent>(TEXT("Arrow"));
	Arrow->ArrowSize = 2.f;
	RootComponent = Arrow;
}

void ALoopManager::BeginPlay()
{
	Super::BeginPlay();

	for (TActorIterator<AAnomaly> It(GetWorld()); It; ++It)
	{
		Anomalies.Add(*It);
		It->SetAnomalyActive(false); // hide every ShowWhenActive actor before the first stage
	}
	if (Stages.IsEmpty())
	{
		UE_LOG(LogEndless, Error, TEXT("LoopManager: Stages is empty, add stages in Details"));
		return;
	}
	EnterStage(FMath::Clamp(DebugStartStage, 0, Stages.Num() - 1));
}

void ALoopManager::CompleteObjective()
{
	bObjectiveDone = true;
}

void ALoopManager::HandleExit(ALoopExit* Exit, APawn* Pawn)
{
	if (bFinished || bTransitioning || Stages.IsEmpty())
	{
		return;
	}
	if (CurrentStage + 1 >= Stages.Num() && (!Stages[CurrentStage].bRequiresObjective || bObjectiveDone))
	{
		bFinished = true; // the finale owns the player now: no teleport, Blueprint decides what is behind the door
		OnFinale.Broadcast();
		return;
	}

	bTransitioning = true;
	if (APlayerController* PC = Cast<APlayerController>(Pawn->GetController()))
	{
		PC->SetIgnoreMoveInput(true);
		PC->SetIgnoreLookInput(true);
		PC->PlayerCameraManager->StartCameraFade(0.f, 1.f, FadeOutTime, FLinearColor::Black, false, true);
	}
	FTimerHandle Timer;
	GetWorldTimerManager().SetTimer(Timer, FTimerDelegate::CreateUObject(this, &ALoopManager::WakeUp, TWeakObjectPtr<APawn>(Pawn)),
		FadeOutTime, false);
}

void ALoopManager::WakeUp(TWeakObjectPtr<APawn> Pawn)
{
	bTransitioning = false;
	if (APawn* P = Pawn.Get())
	{
		// Pivot is on the floor, the capsule center is half its height above it
		P->SetActorLocationAndRotation(GetActorLocation() + FVector(0.f, 0.f, P->GetSimpleCollisionHalfHeight()),
			FRotator(0.f, GetActorRotation().Yaw, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
		if (const ACharacter* Character = Cast<ACharacter>(P))
		{
			Character->GetCharacterMovement()->StopMovementImmediately();
		}
		if (APlayerController* PC = Cast<APlayerController>(P->GetController()))
		{
			PC->SetControlRotation(FRotator(0.f, GetActorRotation().Yaw, 0.f));
			PC->SetIgnoreMoveInput(false);
			PC->SetIgnoreLookInput(false);
			PC->PlayerCameraManager->StartCameraFade(1.f, 0.f, WakeUpTime, FLinearColor::Black);
		}
	}

	// Change the apartment while the screen is still black
	if (Stages[CurrentStage].bRequiresObjective && !bObjectiveDone)
	{
		++RepeatCount;
		UE_LOG(LogEndless, Log, TEXT("Stage %d repeated (%d)"), CurrentStage, RepeatCount);
		OnStageRepeated.Broadcast(CurrentStage, RepeatCount);
		return;
	}
	EnterStage(CurrentStage + 1);
}

void ALoopManager::EnterStage(int32 Stage)
{
	CurrentStage = Stage;
	RepeatCount = 0;
	bObjectiveDone = false;

	for (AAnomaly* Anomaly : Anomalies)
	{
		if (Anomaly)
		{
			Anomaly->ApplyStage(Stage);
		}
	}

	const FString Name = Stages[Stage].Name.ToString();
	UE_LOG(LogEndless, Log, TEXT("Stage %d (%s) started"), Stage, *Name);
#if !UE_BUILD_SHIPPING
	if (bDebugShowStage && GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, FString::Printf(TEXT("Stage %d: %s%s"), Stage, *Name,
			Stages[Stage].bRequiresObjective ? TEXT(" [needs objective]") : TEXT("")));
	}
#endif
	OnStageStarted.Broadcast(Stage);
}
